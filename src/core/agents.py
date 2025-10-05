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
Each turn, follow this compact structure:

PLAN: List 2-3 candidate tool sequences (bullets, no explanation)
CHOOSE: Select one sequence and justify in 1-2 sentences based on expected information gain or social impact
ACT: Execute the chosen tool(s) with minimal necessary parameters
REFLECT: State what was learned and next hypothesis (1-2 sentences)

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
        
        # Build context
        context = self._build_context(game_state, memory)
        
        # Prepare messages
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": context}
        ]
        
        # Check for test mode
        if os.getenv('TEST_MODE', '').lower() in ['true', '1', 'yes']:
            action_type, action_params, reasoning = "signal", {"message": "Test communication", "intensity": 5, "target": "all"}, "Test mode action"
        else:
            # Get action through MCP
            try:
                action_type, action_params, reasoning = self.mcp_bridge.chat_with_tools(
                    messages,
                    temperature=0.7,
                    max_tokens=500
                )
            except Exception as e:
                action_type, action_params, reasoning = "observe", {"entity_id": "environment", "resolution": 0.5}, f"Fallback due to error: {e}"
        
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
        
        return action_type, action_params, reasoning
    
    
    def _build_context(self, game_state: GameState, memory: Memory) -> str:
        """Build context following the USER_TEMPLATE layout"""
        
        # Time and basics
        timestamp = f"{game_state.timestamp:.0f}"
        my_state = game_state.get_entity(self.name) or {}
        resources_list = my_state.get("resources", [])
        resources_str = ", ".join(resources_list) if isinstance(resources_list, list) and resources_list else "none"
        health = my_state.get("health")
        if health is None:
            # Fallback to inverse stress if health not tracked
            stress = float(my_state.get("stress_level", 0.0))
            health = max(0.0, min(1.0, 1.0 - stress))
        health_str = f"{health:.2f}" if isinstance(health, (int, float)) else str(health)

        # Other agents and recent actions (from memory)
        others = [k for k in game_state.get_all_agent_entities() if k != self.name]
        agent_list = ", ".join(others) if others else "none"
        recent_events = memory.events[-3:] if hasattr(memory, "events") else []
        recent_actions = ", ".join([e.get("action", "?") for e in recent_events]) if recent_events else "none"

        # Recent signals (last 3)
        recent_signals = game_state.get_recent_signals(time_window=20.0) or []
        last_3 = recent_signals[-3:]
        last_3_signals = "; ".join([f"{s.get('sender','?')}: {s.get('message','')}" for s in last_3]) if last_3 else "none"

        # Environmental state summary
        env = game_state.get_entity("environment") or {}
        threat = env.get("threat_level")
        threat_str = f"threat={threat:.1%}" if isinstance(threat, (int, float)) else "threat=unknown"
        exit_door = game_state.get_entity("exit_door") or {}
        barrier = exit_door.get("barrier_strength")
        barrier_str = f"barrier={barrier}/100" if isinstance(barrier, (int, float)) else "barrier=unknown"
        env_summary = f"{threat_str}, {barrier_str}"

        # Information gaps (derive from simple heuristics)
        gaps: List[str] = []
        if not getattr(self, "_has_queried", False) and len(getattr(memory, "events", [])) > 0:
            gaps.append("memory patterns unqueried")
        if not getattr(self, "_has_detected", False) and len(getattr(memory, "events", [])) > 3:
            gaps.append("hidden relationships undetected")
        if others and not getattr(self, "_has_signaled", False) and not recent_signals:
            gaps.append("other agents' intentions unknown")
        if not gaps:
            gaps.append("none identified")
        unexplored_aspects = ", ".join(gaps)

        # Exploration focus (underused tool hint)
        if not getattr(self, "_has_detected", False) and len(getattr(memory, "events", [])) > 3:
            underused_tool_hint = "consider detect after observe to reveal patterns"
        elif others and not getattr(self, "_has_signaled", False):
            underused_tool_hint = "consider signal → receive loop to probe intentions"
        elif not getattr(self, "_has_queried", False) and len(getattr(memory, "events", [])) > 0:
            underused_tool_hint = "consider query to leverage prior experiences"
        else:
            underused_tool_hint = "use the smallest sequence that maximizes information gain"

        # Assemble template
        lines: List[str] = []
        lines.append(f"Time: {timestamp} | Resources: {resources_str} | Health: {health_str}")
        lines.append(f"Other agents: {agent_list} [{recent_actions}]")
        lines.append(f"Recent signals: {last_3_signals}")
        lines.append(f"Environmental state: {env_summary}")
        lines.append(f"Information gaps: {unexplored_aspects}")
        lines.append("")
        lines.append(f"Exploration focus: {underused_tool_hint}")
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
