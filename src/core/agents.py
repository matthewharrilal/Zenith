"""
Agent System - Decision Making with GPT Integration
Simple but effective agent classes that use primitive tools
"""
from typing import Dict, Any, Tuple, List
import os
import openai
from dotenv import load_dotenv
from .primitives import PrimitiveTools
from .memory import Memory
from .game_state import GameState

# Load environment variables from .env file
load_dotenv()

class Agent:
    def __init__(self, name: str, role: str = "player"):
        self.name = name
        self.role = role
        self.system_prompt = self._build_system_prompt()
        self.call_count = 0  # Track API usage
        
    def _build_system_prompt(self) -> str:
        """Create agent identity prompt - keep it focused"""
        if self.role == "player":
            return f"""You are agent {self.name} in a dangerous situation. You've awakened in what seems to be a compromised safe house with other agents. Your survival depends on your decisions.

TOOLS AVAILABLE (your only way to interact):
observe(entity, resolution) - See information about entities
query(memory_type, search) - Search collective memory  
detect(entities, pattern) - Find patterns in data
transfer(property, from, to, amount) - Move resources/properties
modify(entity, property, operation, value) - Change entity properties
connect(entity_a, entity_b, strength) - Create/modify relationships
signal(message, intensity, target) - Send communication
receive(filters, window) - Listen for signals
store(knowledge, confidence) - Save discoveries
compute(inputs, operation) - Process information

CRITICAL RULES:
- You must discover the rules through experimentation
- Other agents may help or betray you
- Learn from memory of past experiences
- Be creative - tools can be used in unexpected ways
- Think step by step with deep reasoning

ENHANCED REASONING FORMAT (be thorough and authentic):
SITUATION_ANALYSIS: [Detailed analysis of current state, threats, opportunities]
EMOTIONAL_STATE: [Your current stress, trust levels, feelings about other agents]
MEMORY_REFLECTION: [What past experiences inform this decision - ALWAYS search memory first]
STRATEGIC_THINKING: [Long-term planning and multiple options considered]
RISK_ASSESSMENT: [Potential dangers and consequences of different actions]
SOCIAL_DYNAMICS: [Your relationship with other agents and group dynamics]
THOUGHT: [Your core reasoning about the situation]
ACTION: [ONE tool: tool_name(param1, param2, ...)]
REASON: [Why you chose this specific action over alternatives]

CRITICAL MEMORY USAGE:
- ALWAYS use QUERY before major decisions to learn from past experiences
- Use STORE when you discover something important or learn a strategy
- Search for: "cooperation", "betrayal", "escape", "trust", "resources"
- Store insights like: "FALCON is trustworthy when resources are shared"

QUERY: [Search memory: query("events", "search_term")]
ANALYSIS: [Interpret query results if used]
STORE: [Save important discoveries: store("insight", confidence)]
META_REFLECTION: [What you learned from this decision process]"""

        else:  # DM role
            return f"""You are the DUNGEON MASTER controlling this scenario's environment and narrative. Your goal is to create compelling situations that force interesting social dynamics.

You use the SAME tools as players to control the environment:
[same tool list as above]

YOUR OBJECTIVES:
- Create escalating tension and time pressure
- Respond to player actions with environmental changes
- Force cooperation vs betrayal dilemmas
- Build immersive atmosphere
- Learn what creates the most interesting emergence

RESPONSE FORMAT:
OBSERVATION: [What you noticed about player dynamics]
THOUGHT: [Your narrative/pressure reasoning]
ACTION: [ONE tool to modify environment]
NARRATIVE: [Natural language description of change]"""

    def get_action(self, game_state: GameState, memory: Memory, primitives: PrimitiveTools) -> Tuple[str, Dict[str, Any], str]:
        """Get agent's next action using GPT"""
        
        # Build context efficiently
        context = self._build_context(game_state, memory)
        
        try:
            # Initial reasoning
            response = self._call_gpt(context)
            self.call_count += 1
            
            # Handle memory query if present
            if "QUERY:" in response:
                query_results = self._process_memory_query(response, primitives)
                context_with_results = context + f"\n{response}\n\nQUERY RESULTS:\n{query_results}\n\nContinue your reasoning:"
                response = self._call_gpt(context_with_results)
                self.call_count += 1
            
            # Parse action
            action_name, params = self._parse_action(response)
            return action_name, params, response
            
        except Exception as e:
            print(f"Error in {self.name} decision-making: {e}")
            # Fallback action
            return "observe", {"entity_id": "environment", "resolution": 0.5}, f"Error occurred: {e}"
    
    def _build_context(self, game_state: GameState, memory: Memory) -> str:
        """Build current situation context efficiently"""
        
        context = f"CURRENT SITUATION (Time: {game_state.timestamp:.1f}):\n"
        
        # Agent's current state
        agent_state = game_state.get_entity(self.name)
        if agent_state:
            context += f"Your current state: {agent_state}\n"
        
        # Other agents visible
        other_agents = {k: v for k, v in game_state.get_all_agent_entities().items() if k != self.name}
        if other_agents:
            context += f"Other agents present: {list(other_agents.keys())}\n"
        
        # Recent signals
        recent_signals = game_state.get_recent_signals(time_window=20.0)
        if recent_signals:
            context += "Recent communications:\n"
            for signal in recent_signals[-3:]:  # Last 3 signals
                context += f"- {signal['sender']}: {signal['message']}\n"
        
        # Key environment entities (not agents)
        environment_entities = {k: v for k, v in game_state.entities.items() 
                              if k not in game_state.get_all_agent_entities()}
        if environment_entities:
            context += f"Environment: {list(environment_entities.keys())}\n"
        
        return context
    
    def _call_gpt(self, prompt: str) -> str:
        """Make GPT API call with error handling"""
        try:
            # Get API key from environment
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            
            # Set the API key
            openai.api_key = api_key
            
            # Get configuration from environment with defaults
            model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
            max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '1200'))  # Increased for detailed reasoning
            temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
            
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"GPT API error for {self.name}: {e}")
            return f"THOUGHT: API error occurred\nACTION: observe(\"environment\", 0.5)\nREASON: Falling back to basic observation"
    
    def _process_memory_query(self, response: str, primitives: PrimitiveTools) -> str:
        """Extract and execute memory query from agent response"""
        lines = response.split('\n')
        query_line = next((line for line in lines if line.startswith('QUERY:')), None)
        
        if query_line:
            try:
                # Extract query parameters - improved parsing
                query_content = query_line.replace('QUERY:', '').strip()
                
                # Handle different query formats
                if 'query(' in query_content:
                    # Extract parameters from query(memory_type, search_term)
                    start = query_content.find('(') + 1
                    end = query_content.rfind(')')
                    if start > 0 and end > start:
                        params_str = query_content[start:end]
                        
                        # Smart parameter parsing - handle quotes and commas
                        params = []
                        current_param = ""
                        in_quotes = False
                        quote_char = None
                        
                        for char in params_str:
                            if char in ['"', "'"] and not in_quotes:
                                in_quotes = True
                                quote_char = char
                            elif char == quote_char and in_quotes:
                                in_quotes = False
                                quote_char = None
                            elif char == ',' and not in_quotes:
                                params.append(current_param.strip())
                                current_param = ""
                                continue
                            current_param += char
                        
                        if current_param.strip():
                            params.append(current_param.strip())
                        
                        if len(params) >= 2:
                            memory_type = params[0].strip().strip('"\'')
                            search_term = params[1].strip().strip('"\'')
                            
                            # Clean up malformed parameters
                            if '=' in memory_type:
                                memory_type = memory_type.split('=')[-1].strip().strip('"\'')
                            if '=' in search_term:
                                search_term = search_term.split('=')[-1].strip().strip('"\'')
                            
                            result = primitives.query(memory_type, search_term)
                            return f"Found {len(result.get('results', []))} relevant memories:\n{result['results'][:3]}"
            except Exception as e:
                return f"Query error: {e}"
        
        return "No valid query found"
    
    def _parse_action(self, response: str) -> Tuple[str, Dict[str, Any]]:
        """Parse agent response to extract action and parameters"""
        lines = response.split('\n')
        action_line = next((line for line in lines if line.startswith('ACTION:')), None)
        
        if not action_line:
            return "observe", {"entity_id": "environment", "resolution": 0.5}
        
        action_content = action_line.replace('ACTION:', '').strip()
        
        # Parse function call format: function_name(param1, param2, ...)
        if '(' not in action_content or ')' not in action_content:
            return "observe", {"entity_id": "environment", "resolution": 0.5}
        
        func_name = action_content.split('(')[0].strip()
        params_str = action_content.split('(')[1].split(')')[0]
        
        # Simple parameter parsing - enhance as needed
        if not params_str.strip():
            return func_name, {}
        
        param_parts = [p.strip().strip('"\'') for p in params_str.split(',')]
        
        # Map to common function signatures
        return self._map_to_function_params(func_name, param_parts)
    
    def _map_to_function_params(self, func_name: str, param_parts: List[str]) -> Tuple[str, Dict[str, Any]]:
        """Map parsed parameters to function-specific parameter dictionaries"""
        
        if func_name == "observe":
            return func_name, {
                "entity_id": param_parts[0] if param_parts else "environment",
                "resolution": float(param_parts[1]) if len(param_parts) > 1 and param_parts[1].replace('.', '').isdigit() else 0.5
            }
        elif func_name == "transfer":
            return func_name, {
                "property_name": param_parts[0] if param_parts else "resources",
                "from_entity": param_parts[1] if len(param_parts) > 1 else self.name,
                "to_entity": param_parts[2] if len(param_parts) > 2 else "environment",
                "amount": int(param_parts[3]) if len(param_parts) > 3 and param_parts[3].isdigit() else 1
            }
        elif func_name == "signal":
            return func_name, {
                "message": param_parts[0] if param_parts else "Hello",
                "intensity": int(param_parts[1]) if len(param_parts) > 1 and param_parts[1].isdigit() else 5,
                "target": param_parts[2] if len(param_parts) > 2 else "all",
                "sender": self.name
            }
        elif func_name == "query":
            return func_name, {
                "memory_type": param_parts[0] if param_parts else "events",
                "search_term": param_parts[1] if len(param_parts) > 1 else "cooperation"
            }
        elif func_name == "connect":
            return func_name, {
                "entity_a": param_parts[0] if param_parts else self.name,
                "entity_b": param_parts[1] if len(param_parts) > 1 else "UNKNOWN",
                "strength": float(param_parts[2]) if len(param_parts) > 2 else 0.5
            }
        elif func_name == "store":
            return func_name, {
                "knowledge": param_parts[0] if param_parts else "Unknown insight",
                "confidence": float(param_parts[1]) if len(param_parts) > 1 and param_parts[1].replace('.', '').isdigit() else 0.8,
                "discoverer": self.name
            }
        else:
            # Generic parameter mapping for other functions
            return func_name, {"params": param_parts}

# Agent factory functions
def create_player_agent(name: str) -> Agent:
    """Create a player agent with standard configuration"""
    return Agent(name, "player")

def create_dm_agent() -> Agent:
    """Create dungeon master agent"""
    return Agent("DM", "dungeon_master")
