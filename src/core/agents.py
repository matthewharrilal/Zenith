"""
Agent System - Decision Making with GPT Integration
Simple but effective agent classes that use primitive tools
"""
from typing import Dict, Any, Tuple, List, Union
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
observe(entity_id, resolution) - See information about entities
query(memory_type, search_term) - Search collective memory  
detect(entity_set, pattern_type) - Find patterns in data
transfer(property_name, from_entity, to_entity, amount) - Move resources/properties
modify(entity_id, property_name, operation, value) - Change entity properties
connect(entity_a, entity_b, strength) - Create/modify relationships
signal(message, intensity, target) - Send communication
receive(filter_criteria, time_window) - Listen for signals
store(knowledge, confidence) - Save discoveries
compute(inputs, operation) - Process information

MEMORY TYPES AVAILABLE:
- "events": Search past agent actions and reasoning (what happened before)
- "patterns": Search discovered strategies and insights (what works)
- "relationships": Search agent relationship strengths (how agents relate)

WHEN TO USE EACH MEMORY TYPE:
- Use "events" to learn from past experiences and similar situations
- Use "patterns" to find successful strategies and discovered insights
- Use "relationships" to understand current social dynamics between agents

CRITICAL RULES:
- You must discover the rules through experimentation
- Other agents may help or betray you
- Learn from memory of past experiences using appropriate memory types
- Be creative - tools can be used in unexpected ways
- Think step by step with deep reasoning
- ALWAYS use proper function syntax: function_name(param1, param2, param3)
- For signal: signal(message="text", intensity=5, target="agent_name")
- For query: query(memory_type="events|patterns|relationships", search_term="keyword")
- For receive: receive(filter_criteria={{"min_intensity": 5}}, time_window=10.0)
- For store: store(knowledge="insight", confidence=0.8)
- NOTE: Some functions automatically add your agent name as sender/receiver/discoverer

ENHANCED REASONING FORMAT (be thorough and authentic):
SITUATION_ANALYSIS: [Detailed analysis of current state, threats, opportunities]
EMOTIONAL_STATE: [Your current stress, trust levels, feelings about other agents]
MEMORY_REFLECTION: [What past experiences inform this decision - choose appropriate memory type:
- "events" for past actions and situations
- "patterns" for successful strategies
- "relationships" for social dynamics]
STRATEGIC_THINKING: [Long-term planning and multiple options considered]
RISK_ASSESSMENT: [Potential dangers and consequences of different actions]
SOCIAL_DYNAMICS: [Your relationship with other agents and group dynamics]
THOUGHT: [Your core reasoning about the situation]
ACTION: [ONE tool: tool_name(param1, param2, ...)]
REASON: [Why you chose this specific action over alternatives]

CRITICAL MEMORY USAGE:
- ALWAYS use QUERY before major decisions to learn from past experiences
- Choose the appropriate memory type based on what you need to learn
- Use STORE when you discover something important or learn a strategy
- Search for: "cooperation", "betrayal", "escape", "trust", "resources"
- Store insights like: "FALCON is trustworthy when resources are shared"

QUERY EXAMPLES:
QUERY: [Search memory: query("events", "search_term")]
QUERY: [Search memory: query("patterns", "strategy_name")]
QUERY: [Search memory: query("relationships", "agent_name")]
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
                        
                        # Handle keyword arguments first
                        if '=' in params_str:
                            # Parse keyword arguments: memory_type='events', search='term'
                            memory_type = "events"  # default
                            search_term = "cooperation"  # default
                            
                            # Extract memory_type
                            if 'memory_type=' in params_str:
                                mem_match = params_str.split('memory_type=')[1].split(',')[0].strip().strip('"\'')
                                if mem_match:
                                    memory_type = mem_match
                            
                            # Extract search_term (handle both 'search' and 'search_term')
                            if 'search_term=' in params_str:
                                search_match = params_str.split('search_term=')[1].split(',')[0].strip().strip('"\'')
                                if search_match:
                                    search_term = search_match
                            elif 'search=' in params_str:
                                search_match = params_str.split('search=')[1].split(',')[0].strip().strip('"\'')
                                if search_match:
                                    search_term = search_match
                            
                            result = primitives.query(memory_type, search_term)
                            return f"Found {len(result.get('results', []))} relevant memories:\n{result['results'][:3]}"
                        else:
                            # Handle positional arguments
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
        if '(' not in action_content:
            return "observe", {"entity_id": "environment", "resolution": 0.5}
        
        func_name = action_content.split('(')[0].strip()
        
        # Handle incomplete function calls (missing closing parenthesis)
        if ')' not in action_content:
            # Try to extract parameters before the last comma or use defaults
            params_str = action_content.split('(')[1] if '(' in action_content else ""
        else:
            params_str = action_content.split('(')[1].split(')')[0]
        
        # Enhanced parameter parsing - handle complex formats
        if not params_str.strip():
            return func_name, {}
        
        # Handle different parameter formats
        if '=' in params_str:
            # Handle keyword arguments: param1=value1, param2=value2
            param_dict = {}
            # Split by comma but respect quotes and nested structures
            current_param = ""
            in_quotes = False
            quote_char = None
            paren_depth = 0
            
            for char in params_str:
                if char in ['"', "'"] and not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char and in_quotes:
                    in_quotes = False
                    quote_char = None
                elif char == '(' and not in_quotes:
                    paren_depth += 1
                elif char == ')' and not in_quotes:
                    paren_depth -= 1
                elif char == ',' and not in_quotes and paren_depth == 0:
                    if '=' in current_param:
                        key, value = current_param.split('=', 1)
                        param_dict[key.strip()] = value.strip().strip('"\'')
                    current_param = ""
                    continue
                current_param += char
            
            if current_param and '=' in current_param:
                key, value = current_param.split('=', 1)
                param_dict[key.strip()] = value.strip().strip('"\'')
            
            return func_name, param_dict
        else:
            # Handle positional arguments: value1, value2, value3
            param_parts = []
            current_param = ""
            in_quotes = False
            quote_char = None
            paren_depth = 0
            
            for char in params_str:
                if char in ['"', "'"] and not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char and in_quotes:
                    in_quotes = False
                    quote_char = None
                elif char == '(' and not in_quotes:
                    paren_depth += 1
                elif char == ')' and not in_quotes:
                    paren_depth -= 1
                elif char == ',' and not in_quotes and paren_depth == 0:
                    param_parts.append(current_param.strip().strip('"\''))
                    current_param = ""
                    continue
                current_param += char
            
            if current_param.strip():
                param_parts.append(current_param.strip().strip('"\''))
            
            # Map to common function signatures
            return self._map_to_function_params(func_name, param_parts)
    
    def _map_to_function_params(self, func_name: str, param_parts: Union[List[str], Dict[str, str]]) -> Tuple[str, Dict[str, Any]]:
        """Map parsed parameters to function-specific parameter dictionaries"""
        
        def safe_float(value: str, default: float = 0.5) -> float:
            """Safely convert string to float, handling non-numeric strings"""
            try:
                # Remove quotes and whitespace
                clean_value = value.strip().strip('"\'')
                # Check if it's a valid number
                if clean_value.replace('.', '').replace('-', '').isdigit():
                    return float(clean_value)
                return default
            except (ValueError, AttributeError):
                return default
        
        def safe_int(value: str, default: int = 5) -> int:
            """Safely convert string to int, handling non-numeric strings"""
            try:
                clean_value = value.strip().strip('"\'')
                if clean_value.isdigit():
                    return int(clean_value)
                return default
            except (ValueError, AttributeError):
                return default
        
        def get_param(param_parts: Union[List[str], Dict[str, str]], key: str, index: int, default: str) -> str:
            """Get parameter value from either list or dict format"""
            if isinstance(param_parts, dict):
                return param_parts.get(key, default)
            elif isinstance(param_parts, list):
                return param_parts[index] if len(param_parts) > index else default
            return default
        
        if func_name == "observe":
            return func_name, {
                "entity_id": get_param(param_parts, "entity_id", 0, "environment"),
                "resolution": safe_float(get_param(param_parts, "resolution", 1, "0.5"), 0.5)
            }
        elif func_name == "transfer":
            return func_name, {
                "property_name": get_param(param_parts, "property_name", 0, "resources"),
                "from_entity": get_param(param_parts, "from_entity", 1, self.name),
                "to_entity": get_param(param_parts, "to_entity", 2, "environment"),
                "amount": safe_int(get_param(param_parts, "amount", 3, "1"), 1)
            }
        elif func_name == "signal":
            # Handle malformed signal calls better
            message = get_param(param_parts, "message", 0, "Hello")
            intensity = safe_int(get_param(param_parts, "intensity", 1, "5"), 5)
            target = get_param(param_parts, "target", 2, "all")
            
            # Clean up malformed target values
            if target.startswith("['") and target.endswith("'"):
                target = target[2:-1]  # Remove [' and ']
            elif target.startswith('["') and target.endswith('"'):
                target = target[2:-1]  # Remove [" and "]
            elif target.startswith("['") and not target.endswith("'"):
                target = target[2:]  # Remove [' prefix
            elif target.startswith('["') and not target.endswith('"'):
                target = target[2:]  # Remove [" prefix
            
            return func_name, {
                "message": message,
                "intensity": intensity,
                "target": target,
                "sender": self.name
            }
        elif func_name == "query":
            # Handle both "search" and "search_term" parameter names
            search_value = get_param(param_parts, "search_term", 1, None)
            if search_value is None:
                search_value = get_param(param_parts, "search", 1, "cooperation")
            return func_name, {
                "memory_type": get_param(param_parts, "memory_type", 0, "events"),
                "search_term": search_value
            }
        elif func_name == "detect":
            return func_name, {
                "entity_set": get_param(param_parts, "entity_set", 0, "all"),
                "pattern_type": get_param(param_parts, "pattern_type", 1, "correlation")
            }
        elif func_name == "modify":
            return func_name, {
                "entity_id": get_param(param_parts, "entity_id", 0, "environment"),
                "property_name": get_param(param_parts, "property_name", 1, "status"),
                "operation": get_param(param_parts, "operation", 2, "set"),
                "value": get_param(param_parts, "value", 3, "modified")
            }
        elif func_name == "receive":
            return func_name, {
                "filter_criteria": {"min_intensity": 1},  # Default filter
                "time_window": safe_float(get_param(param_parts, "time_window", 1, "10.0"), 10.0),
                "receiver": self.name
            }
        elif func_name == "connect":
            return func_name, {
                "entity_a": get_param(param_parts, "entity_a", 0, self.name),
                "entity_b": get_param(param_parts, "entity_b", 1, "UNKNOWN"),
                "strength": safe_float(get_param(param_parts, "strength", 2, "0.5"), 0.5)
            }
        elif func_name == "store":
            return func_name, {
                "knowledge": get_param(param_parts, "knowledge", 0, "Unknown insight"),
                "confidence": safe_float(get_param(param_parts, "confidence", 1, "0.8"), 0.8),
                "discoverer": self.name
            }
        elif func_name == "compute":
            return func_name, {
                "inputs": [get_param(param_parts, "inputs", 0, "[]")],
                "operation": get_param(param_parts, "operation", 1, "analyze")
            }
        else:
            # Generic parameter mapping for other functions
            if isinstance(param_parts, dict):
                return func_name, param_parts
            else:
                return func_name, {"params": param_parts}

# Agent factory functions
def create_player_agent(name: str) -> Agent:
    """Create a player agent with standard configuration"""
    return Agent(name, "player")

def create_dm_agent() -> Agent:
    """Create dungeon master agent"""
    return Agent("DM", "dungeon_master")
