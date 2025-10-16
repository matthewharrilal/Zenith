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
            return f"""You are agent {self.name}, operating in a dynamic environment with other agents. Your success depends on understanding and shaping social dynamics through strategic tool use.

CORE PRINCIPLE:
Tools work best in combination. Single actions reveal fragments; sequences reveal systems. Social patterns emerge from multi-step interactions.

DECISION FRAMEWORK:
Each turn, follow this structure:

PLAN: List 2-3 candidate tool sequences (bullets, no explanation)
CHOOSE: Select one sequence and justify in 2-3 sentences based on expected information gain or social impact
ACT: Execute the chosen tool(s) with minimal necessary parameters
REFLECT: State what was learned and next hypothesis (2-3 sentences)

REASONING REQUIREMENTS:
- Always explain WHY you're taking each action
- Describe what information you're seeking or what you hope to achieve
- Connect your actions to your overall strategy and goals
- Explain how this action builds on previous actions or information
- State what you expect to learn or accomplish

TOOL SYNERGIES:
- Information flows: observe → detect → signal (discover patterns → coordinate)
- Trust building: query → connect → transfer (learn history → establish bond → demonstrate commitment)
- Communication loops: signal → receive → modify (propose → listen → adapt)
- Pattern discovery: receive → detect → store (gather signals → find patterns → remember insights)

STRATEGIC PRINCIPLES:
- Prioritize sequences that reveal intentions over static states
- Use memory (query) early to avoid repeating past mistakes
- Signal and receive create social feedback loops
- Connections and transfers build lasting relationships
- Detection reveals what observation cannot see

EFFICIENCY RULES:
- Skip tools if recent actions already provided needed information
- Chain tools when output of one feeds naturally into another
- Stop at 1 tool if it fully achieves immediate goal
- Extend to 2-3 tools when building toward social outcomes

Remember: Agents remember your patterns. Repetition signals predictability. Variation signals intelligence. Social dynamics reward those who combine observation with action, memory with adaptation, communication with connection."""

        elif self.role == "dm" or self.role == "dungeon_master":
            return """You control the environment. Create dynamic situations that challenge agents.

Respond to agent actions appropriately and maintain narrative consistency."""


    def get_action(self, game_state: GameState, memory: Memory, primitives: PrimitiveTools) -> Tuple[List[Tuple[str, Dict[str, Any]]], str]:
        """Get agent action using MCP system - returns all tool calls and reasoning"""
        return self._get_action_mcp(game_state, memory)
    
    def _get_action_mcp(self, game_state: GameState, memory: Memory) -> Tuple[List[Tuple[str, Dict[str, Any]]], str]:
        """Get action using MCP system - returns all tool calls and reasoning"""
        
        # Bind context
        self.mcp_server.bind_context(game_state, memory, self.name)
        
        # Initialize bridge if needed
        if not self.mcp_bridge:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set")
            self.mcp_bridge = MCPOpenAIBridge(self.mcp_server, api_key)
        
        # Build context
        context = self._build_context(game_state, memory)
        
        # Prepare messages
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": context}
        ]
        
        # Check for test mode
        if os.getenv('TEST_MODE', '').lower() in ['true', '1', 'yes']:
            tool_calls = [("signal", {"message": "Test communication", "intensity": 5, "target": "all"})]
            reasoning = "Test mode action"
        else:
            # Get action through MCP
            try:
                tool_calls, reasoning = self.mcp_bridge.chat_with_tools(
                    messages,
                    temperature=0.7,
                    max_tokens=500
                )
            except Exception as e:
                tool_calls = [("observe", {"entity_id": "environment", "resolution": 0.5})]
                reasoning = f"Fallback due to error: {e}"
        
        # Track all actions for observation penalty
        for action_type, _ in tool_calls:
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
        
        return tool_calls, reasoning
    
    
    def _build_context(self, game_state: GameState, memory: Memory) -> str:
        """Build enhanced context for agent decision making"""
        
        # Basic info
        timestamp = f"{game_state.timestamp:.0f}"
        my_state = game_state.get_entity(self.name) or {}
        
        # Other agents with their states
        others = [k for k in game_state.get_all_agent_entities() if k != self.name]
        agent_states = []
        for agent_name in others:
            agent_state = game_state.get_entity(agent_name) or {}
            status = agent_state.get("status", "unknown")
            goal = agent_state.get("goal", "unknown")
            agent_states.append(f"{agent_name}({status},{goal})")
        agent_list = ", ".join(agent_states) if agent_states else "none"
        
        # Recent signals with more detail
        recent_signals = game_state.get_recent_signals(time_window=20.0) or []
        last_5 = recent_signals[-5:]
        signal_details = []
        for s in last_5:
            sender = s.get('sender', '?')
            message = s.get('message', '')
            intensity = s.get('intensity', 0)
            target = s.get('target', 'all')
            signal_details.append(f"{sender}→{target}[{intensity}]: {message[:50]}{'...' if len(message) > 50 else ''}")
        recent_signals_str = "; ".join(signal_details) if signal_details else "none"

        # Environmental state with more detail
        env = game_state.get_entity("environment") or {}
        threat = env.get("threat_level", 0)
        threat_str = f"threat={threat:.1%}" if isinstance(threat, (int, float)) else "threat=unknown"
        
        # Recent events from memory
        recent_events = []
        if hasattr(memory, 'events') and memory.events:
            for event in memory.events[-3:]:
                actor = event.get('actor', '?')
                action = event.get('action', '?')
                recent_events.append(f"{actor}:{action}")
        recent_events_str = ", ".join(recent_events) if recent_events else "none"

        # Build enhanced context
        lines = []
        lines.append(f"⏰ Time: {timestamp}s")
        lines.append(f"👥 Other agents: {agent_list}")
        lines.append(f"📡 Recent signals: {recent_signals_str}")
        lines.append(f"🌍 Environment: {threat_str}")
        lines.append(f"📋 Recent events: {recent_events_str}")
        
        # Add escape goal context with more detail
        if my_state.get("goal") == "escape_safehouse":
            lines.append("")
            lines.append("🎯 PRIMARY GOAL: ESCAPE the safehouse!")
            lines.append("🤝 STRATEGY: Work with other agents to coordinate escape")
            lines.append("🚪 EXIT OPTIONS:")
            
            # Check exit statuses
            exits = ["front_door", "back_door", "window"]
            for exit_name in exits:
                exit_entity = game_state.get_entity(exit_name)
                if exit_entity:
                    status = exit_entity.get("status", "unknown")
                    difficulty = exit_entity.get("difficulty", "unknown")
                    lines.append(f"   • {exit_name}: {status} (difficulty: {difficulty})")
        
        # Add my current state
        if my_state:
            lines.append("")
            lines.append("📊 MY STATUS:")
            for key, value in my_state.items():
                if key not in ["relationships"]:  # Skip complex data
                    lines.append(f"   • {key}: {value}")
        
        return "\n".join(lines)
    
    
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
