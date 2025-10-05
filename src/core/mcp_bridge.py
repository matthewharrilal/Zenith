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
        
        
        # Add diversity hint based on usage, not tool names
        diversity_hint = self._get_diversity_hint()
        if diversity_hint:
            # Add as user message for more impact
            if messages and messages[-1]["role"] == "user":
                messages[-1]["content"] += f"\n\nIMPORTANT: {diversity_hint}"
            else:
                messages.append({
                    "role": "user", 
                    "content": f"IMPORTANT: {diversity_hint}"
                })
        
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
            
            # Return the first tool call info and final response
            first_tool_call = message.tool_calls[0]
            first_arguments = json.loads(first_tool_call.function.arguments)
            
            # Track successful tool usage
            tool_name = first_tool_call.function.name
            self._tool_usage_count[tool_name] = self._tool_usage_count.get(tool_name, 0) + 1
            
            final_content = final.choices[0].message.content
            if final_content is None:
                final_content = "No response generated"
            
            return (
                first_tool_call.function.name,
                first_arguments,
                final_content
            )
        
        content = message.content
        if content is None:
            content = "No response generated"
        
        # FORCE ACTION: If no tool calls were made, force a default action
        # This prevents analysis paralysis by ensuring agents always act
        print(f"⚠️  No tool calls made, forcing default action")
        
        # Use diversity-aware fallback
        forced_action, forced_params = self._get_diversity_fallback()
        self._tool_usage_count[forced_action] = self._tool_usage_count.get(forced_action, 0) + 1
        
        return forced_action, forced_params, content
    
    def _get_diversity_hint(self) -> Optional[str]:
        """Frame diversity as necessary, not optional"""
        import random
        
        if not self._tool_usage_count:
            return "EXPLORE: Each tool reveals different information. Observation shows what IS, communication reveals intentions, memory shows patterns, detection finds relationships."
        
        # Check for observe dominance specifically
        observe_count = self._tool_usage_count.get('observe', 0)
        total = sum(self._tool_usage_count.values())
        
        if observe_count > 0 and observe_count == total:
            return "EXPLORE: Pure observation is passive. Try communication (signal/receive), memory queries, or pattern detection to understand WHY and HOW."
        
        if observe_count > total * 0.5:
            return "EXPLORE: Watching without engaging limits understanding. Communication reveals intentions, memory shows patterns, detection finds relationships."
        
        # Check for communication dominance
        comm_count = self._tool_usage_count.get('signal', 0) + self._tool_usage_count.get('receive', 0)
        if comm_count > total * 0.6:
            return "EXPLORE: Communication is good, but try observation to see current state, memory queries to learn from past, or pattern detection to find hidden connections."
        
        # General diversity push
        unique = len(self._tool_usage_count)
        if unique < 3:
            return "EXPLORE: Limited approaches create blind spots. Try different tools - each reveals different aspects of reality."
        
        # Encourage deeper exploration
        if unique >= 4:
            return "DEEPEN: You're using diverse tools. Now try combining them - query memory about past observations, signal about discovered patterns, or detect relationships between different entities."
        
        return None
    
    def _get_forced_rotation_tool(self) -> Optional[str]:
        """Force rotation when stuck on one tool"""
        if not self._tool_usage_count:
            return None
        
        # Get the overused tool
        overused_tool = max(self._tool_usage_count, key=self._tool_usage_count.get)
        
        # Rotation sequence - different from overused
        rotation_sequence = ["signal", "receive", "query", "modify", "connect", "detect", "store", "compute", "transfer", "observe"]
        
        # Find next tool in sequence
        try:
            current_index = rotation_sequence.index(overused_tool)
            next_tool = rotation_sequence[(current_index + 1) % len(rotation_sequence)]
            return next_tool
        except ValueError:
            # If overused tool not in sequence, return first non-overused
            for tool in rotation_sequence:
                if tool != overused_tool:
                    return tool
            return None
    
    def _get_diversity_fallback(self) -> Tuple[str, Dict[str, Any]]:
        """Get diversity-aware fallback action with philosophical variety"""
        import random
        
        if not self._tool_usage_count:
            return "signal", {"message": "Hello, exploring communication", "intensity": 5, "target": "all"}
        
        # Find least used tool
        min_usage = min(self._tool_usage_count.values())
        least_used = [tool for tool, count in self._tool_usage_count.items() if count == min_usage]
        
        # If only one tool used, force a different one
        if len(self._tool_usage_count) == 1:
            if "observe" in self._tool_usage_count:
                return "signal", {"message": "Exploring communication", "intensity": 5, "target": "all"}
            elif "signal" in self._tool_usage_count:
                return "receive", {"filter_criteria": {}, "time_window": 10.0}
            elif "receive" in self._tool_usage_count:
                return "query", {"memory_type": "events", "search_term": "exploration"}
            else:
                return "observe", {"entity_id": "environment", "resolution": 0.5}
        
        # Rotate through least used tools with some randomness
        available_tools = ["signal", "receive", "query", "observe", "modify", "connect", "detect", "store", "compute", "transfer"]
        unused_tools = [tool for tool in available_tools if tool not in self._tool_usage_count]
        
        if unused_tools:
            # Prefer completely unused tools
            tool = random.choice(unused_tools)
        else:
            # Use least used
            tool = random.choice(least_used)
        
        # Generate appropriate parameters
        if tool == "signal":
            return "signal", {"message": "Exploring communication", "intensity": 5, "target": "all"}
        elif tool == "receive":
            return "receive", {"filter_criteria": {}, "time_window": 10.0}
        elif tool == "query":
            return "query", {"memory_type": "events", "search_term": "exploration"}
        elif tool == "observe":
            return "observe", {"entity_id": "environment", "resolution": 0.5}
        elif tool == "modify":
            return "modify", {"entity_id": "environment", "changes": {"exploration": True}}
        elif tool == "connect":
            return "connect", {"target_entity": "environment", "connection_type": "exploration"}
        elif tool == "detect":
            return "detect", {"detection_type": "exploration", "range": 10.0}
        elif tool == "store":
            return "store", {"data": {"exploration": True}, "location": "memory"}
        elif tool == "compute":
            return "compute", {"operation": "exploration", "inputs": ["environment"]}
        elif tool == "transfer":
            return "transfer", {"source": "environment", "target": "memory", "data": {"exploration": True}}
        else:
            return "signal", {"message": "Exploring communication", "intensity": 5, "target": "all"}
