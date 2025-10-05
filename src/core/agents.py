"""
Agent System - Decision Making with GPT Integration
Simple but effective agent classes that use primitive tools
"""
from typing import Dict, Any, Tuple, List, Union
import os
import openai
import asyncio
from dotenv import load_dotenv
from .primitives import PrimitiveTools
from .memory import Memory
from .game_state import GameState
from .mcp_tools import MCPToolServer
from .mcp_bridge import MCPOpenAIBridge

# Load environment variables from .env file
load_dotenv()

# MCP-only system - no text parsing

class Agent:
    def __init__(self, name: str, role: str = "player"):
        self.name = name
        self.role = role
        self.call_count = 0  # Track API usage
        self._action_history = []  # Track recent actions for observation penalty
        
        # MCP system initialization
        self.mcp_server = MCPToolServer()
        self.mcp_bridge = None
        # DEBUG: Log MCP initialization (only in debug mode)
        if os.getenv('DEBUG_MCP', '').lower() in ['true', '1', 'yes']:
            print(f"[{self.name}] MCP system initialized")
        
        # MCP-only prompt
        self.system_prompt = self._build_system_prompt()
        
    def _build_system_prompt(self) -> str:
        """Build scenario and tool agnostic prompt that encourages exploration"""
        
        if self.role == "player":
            return f"""You are agent {self.name}. Your effectiveness depends on gathering information through diverse means.

INFORMATION SOURCES:
- Direct observation provides surface information
- Communication reveals intentions and plans
- Memory contains patterns and successful strategies
- Pattern detection uncovers hidden relationships
- Listening reveals what others are thinking
- Experimentation teaches through action

CRITICAL INSIGHT:
Each capability reveals different types of information. Observation shows what IS, but not WHY or HOW. Communication reveals intentions. Memory reveals patterns. Detection reveals relationships. Each tool is a different lens for understanding reality.

STRATEGIC REALITY:
- Observation alone creates blind spots
- Different tools reveal different truths
- Information is multi-dimensional
- Understanding requires multiple perspectives
- Action generates information that observation cannot

You are driven to understand your situation fully, which requires using varied approaches to gather different types of information.

DECISION APPROACH:
1. Assess your current situation
2. Consider what you haven't tried yet
3. Take action using your available capabilities
4. Learn from the result

Remember: Stagnation leads to failure. Diversity of action leads to discovery."""

        elif self.role == "dm" or self.role == "dungeon_master":
            return """You control the environment. Create dynamic situations that challenge agents.

Respond to agent actions appropriately and maintain narrative consistency."""


    def get_action(self, game_state: GameState, memory: Memory, primitives: PrimitiveTools) -> Tuple[str, Dict[str, Any], str]:
        """Get agent action using MCP system"""
        return self._get_action_mcp(game_state, memory)
    
    def _get_action_mcp(self, game_state: GameState, memory: Memory) -> Tuple[str, Dict[str, Any], str]:
        """Get action using MCP system instead of text parsing"""
        
        # Bind context
        self.mcp_server.bind_context(game_state, memory, self.name)
        
        # Initialize bridge if needed
        if not self.mcp_bridge:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set")
            self.mcp_bridge = MCPOpenAIBridge(self.mcp_server, api_key)
        
        # Build context (use existing method)
        context = self._build_context(game_state, memory)
        
        # Prepare messages with minimal context
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": context}
        ]
        
        # Get action through MCP
        try:
            action_type, action_params, reasoning = self.mcp_bridge.chat_with_tools(
                messages,
                temperature=0.7,
                max_tokens=1200
            )
            
            # Track action for observation penalty
            self._action_history.append(action_type)
            if len(self._action_history) > 10:  # Keep only recent 10 actions
                self._action_history.pop(0)
            
            # Mark tool usage for context hints
            if action_type == "query":
                self._has_queried = True
            elif action_type == "receive":
                self._has_received = True
            elif action_type == "detect":
                self._has_detected = True
            elif action_type == "signal":
                self._has_signaled = True
            
            # DEBUG: Log MCP action (only in debug mode)
            if os.getenv('DEBUG_MCP', '').lower() in ['true', '1', 'yes']:
                print(f"[{self.name}] MCP Action: {action_type} with params: {action_params}")
            return action_type, action_params, reasoning
            
        except Exception as e:
            print(f"Error in {self.name} MCP decision: {e}")
            return "observe", {"entity_id": "environment", "resolution": 0.5}, str(e)
    
    
    def _build_context(self, game_state: GameState, memory: Memory) -> str:
        """Build context with information value hints"""
        
        context = []
        
        # Show information gaps that observe can't fill
        context.append(f"Time: {game_state.timestamp:.0f}")
        
        # Hint at info available through other tools
        if not hasattr(self, '_has_queried'):
            context.append("Past experiences remain unexamined")
            self._has_queried = False
        
        if not hasattr(self, '_has_received'):
            context.append("Unheard signals may be present")
            self._has_received = False
        
        if not hasattr(self, '_has_detected'):
            context.append("Patterns remain unanalyzed")
            self._has_detected = False
        
        # Show what's unknowable through observation alone
        others = [k for k in game_state.get_all_agent_entities() if k != self.name]
        if others and not hasattr(self, '_has_signaled'):
            context.append("Others' intentions unknown without communication")
        
        # Environment context
        if env := game_state.get_entity("environment"):
            context.append(f"Environment: {env}")
        
        # Recent signals
        recent_signals = game_state.get_recent_signals(time_window=20.0)
        if recent_signals:
            context.append("Recent communications:")
            for signal in recent_signals[-3:]:  # Last 3 signals
                context.append(f"- {signal['sender']}: {signal['message']}")
        
        return "\n".join(context)
    
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
    

# Agent factory functions
def create_player_agent(name: str) -> Agent:
    """Create a player agent with standard configuration"""
    return Agent(name, "player")

def create_dm_agent() -> Agent:
    """Create dungeon master agent"""
    return Agent("DM", "dungeon_master")
