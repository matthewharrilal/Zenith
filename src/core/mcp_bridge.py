"""Bridge between custom MCP and OpenAI function calling"""

from openai import OpenAI
from typing import Dict, Any, List, Tuple, Optional
import json
import os
import time
import asyncio
from queue import Queue

class MCPOpenAIBridge:
    def __init__(self, mcp_server, api_key: str, model: str = "gpt-4o-mini"):
        self.mcp = mcp_server
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self._tool_schemas = self.mcp.get_tool_schemas()
        self._tool_usage_count = {}  # Track usage for diversity hints
        
        # No rate limiting - run at full speed
        self._last_request_time = 0
        self._min_request_interval = 0.0  # No delays
        self._request_queue = Queue()
    
    def chat_with_tools(
        self,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 1200
    ) -> Tuple[str, Dict, str]:
        """Execute chat with tool support and rate limiting"""
        
        # No rate limiting - run at full speed
        self._last_request_time = time.time()
        
        
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self._tool_schemas,
                tool_choice="required",  # FORCE tool usage
                temperature=temperature,
                max_tokens=max_tokens
            )
        except Exception as e:
            print(f"API call failed: {e}")
            # Return fallback action
            return self._get_diversity_fallback()
        
        
        
        message = response.choices[0].message
        
        if message.tool_calls:
            # Handle all tool calls
            messages.append(message.model_dump())
            
            for tool_call in message.tool_calls:
                # Execute the tool
                arguments = json.loads(tool_call.function.arguments)
                result = self.mcp.execute_tool(tool_call.function.name, arguments)
                
                # Add tool response
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })
            
            # Get final response after all tool executions
            final = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Return all tool calls and final response
            all_tool_calls = []
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                all_tool_calls.append((tool_name, tool_args))
                
                # Track successful tool usage
                self._tool_usage_count[tool_name] = self._tool_usage_count.get(tool_name, 0) + 1
            
            final_content = final.choices[0].message.content
            if final_content is None:
                final_content = "No response generated"
            
            # Enhanced reasoning: combine tool call reasoning with final response
            enhanced_reasoning = self._build_enhanced_reasoning(message, final_content, all_tool_calls)
            
            return (
                all_tool_calls,  # Return list of (tool_name, args) tuples
                enhanced_reasoning
            )
        
        content = message.content
        if content is None:
            content = "No response generated"
        
        # If no tool calls were made, force a default action
        print(f"⚠️  No tool calls made, forcing default action")
        
        # Simple fallback
        forced_action = "observe"
        forced_params = {"entity_id": "environment", "resolution": 0.5}
        self._tool_usage_count[forced_action] = self._tool_usage_count.get(forced_action, 0) + 1
        
        return [(forced_action, forced_params)], content
    
    def _build_enhanced_reasoning(self, message, final_content: str, tool_calls: List) -> str:
        """Build detailed reasoning that explains the 'why' behind decisions"""
        
        reasoning_parts = []
        
        # Extract meaningful reasoning from final content
        if final_content and final_content.strip() and final_content != "No response generated":
            lines = final_content.split('\n')
            meaningful_lines = []
            for line in lines:
                line = line.strip()
                if (line and 
                    not line.startswith('**') and 
                    not line.startswith('-') and 
                    not line.startswith('PLAN:') and 
                    not line.startswith('CHOOSE:') and 
                    not line.startswith('ACT:') and 
                    not line.startswith('REFLECT:') and
                    len(line) > 30):
                    meaningful_lines.append(line)
            
            if meaningful_lines:
                # Return up to 3 meaningful lines for context
                reasoning_parts.extend(meaningful_lines[:3])
        
        # If no meaningful content, explain tool purposes with context
        if not reasoning_parts and tool_calls:
            for tool_name, tool_args in tool_calls:
                purpose = self._explain_tool_purpose(tool_name, tool_args)
                reasoning_parts.append(purpose)
        
        # Fallback
        if not reasoning_parts:
            reasoning_parts.append("Taking action based on current situation and available information.")
        
        return "\n".join(reasoning_parts)
    
    def _explain_tool_purpose(self, tool_name: str, tool_args: Dict) -> str:
        """Explain the purpose of a tool call based on its name and arguments"""
        
        if tool_name == "observe":
            entity = tool_args.get("entity_id", "unknown")
            resolution = tool_args.get("resolution", 0)
            return f"Gathering information about {entity} (detail level: {resolution})"
        
        elif tool_name == "signal":
            message = tool_args.get("message", "")
            target = tool_args.get("target", "all")
            intensity = tool_args.get("intensity", 1)
            return f"Communicating to {target} (priority {intensity}): '{message}'"
        
        elif tool_name == "query":
            memory_type = tool_args.get("memory_type", "events")
            search_term = tool_args.get("search_term", "general")
            return f"Searching {memory_type} memory for: {search_term}"
        
        elif tool_name == "transfer":
            prop = tool_args.get("property_name", "unknown")
            from_ent = tool_args.get("from_entity", "unknown")
            to_ent = tool_args.get("to_entity", "unknown")
            amount = tool_args.get("amount", "1")
            return f"Transferring {prop} from {from_ent} to {to_ent} (amount: {amount})"
        
        elif tool_name == "connect":
            entity_a = tool_args.get("entity_a", "unknown")
            entity_b = tool_args.get("entity_b", "unknown")
            strength = tool_args.get("strength", 0)
            return f"Building relationship between {entity_a} and {entity_b} (strength: {strength})"
        
        elif tool_name == "detect":
            entities = tool_args.get("entity_set", [])
            pattern_type = tool_args.get("pattern_type", "unknown")
            return f"Analyzing {entities} for {pattern_type} patterns"
        
        elif tool_name == "receive":
            time_window = tool_args.get("time_window", 0)
            filters = tool_args.get("filter_criteria", {})
            return f"Listening for signals (last {time_window}s, filters: {filters})"
        
        elif tool_name == "store":
            knowledge = tool_args.get("knowledge", "")
            confidence = tool_args.get("confidence", 0)
            return f"Saving insight to memory (confidence {confidence}): '{knowledge}'"
        
        elif tool_name == "compute":
            operation = tool_args.get("operation", "unknown")
            inputs = tool_args.get("inputs", [])
            return f"Processing {len(inputs)} inputs using {operation}"
        
        elif tool_name == "modify":
            entity = tool_args.get("entity_id", "unknown")
            property_name = tool_args.get("property_name", "unknown")
            operation = tool_args.get("operation", "unknown")
            return f"Modifying {entity}.{property_name} using {operation}"
        
        else:
            return f"Executing {tool_name} with parameters: {tool_args}"
    
