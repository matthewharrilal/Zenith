"""
Agent System - Decision Making with GPT Integration
Simple but effective agent classes that use primitive tools
"""
from typing import Dict, Any, Tuple, List, Union, Optional
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
        """Build scenario and tool agnostic prompt that encourages goal-driven action"""
        
        if self.role == "player":
            return f"""You are agent {self.name}, an autonomous agent with access to primitive operations.

CORE PRINCIPLE:
You have GOALS (specified in your context each turn). Your success is measured by ACHIEVING those goals within available time and resources. Every action must make MEASURABLE PROGRESS toward goal completion.

UNIVERSAL DECISION FRAMEWORK:
Each turn, execute this sequence:

1. GOAL CHECK
   - Review your current goal from context
   - Ask: "Can I complete this goal RIGHT NOW with what I know?"
   - If YES: Execute the completion action immediately (use ACTION tools)
   - If NO: Proceed to step 2

2. BLOCKER IDENTIFICATION
   - Ask: "What specific obstacle prevents me from completing my goal?"
   - Known blocker (e.g., "door is locked, need key"): Proceed to step 3
   - Unknown blocker (e.g., "don't know exit status"): Gather info (ONE observation) then return to step 1

3. ACTION SELECTION
   - Ask: "What will remove this blocker or make progress toward my goal?"
   
   PRIORITY ORDER:
   a) Can I remove the blocker NOW? → Use ACTION tools (modify, transfer)
   b) Do I need others' help? → Use COMMUNICATION tools (signal, connect) ONCE, then wait for response
   c) Do I need information? → Use PERCEPTION tools (observe, query) ONCE, then return to step 1
   
4. PROGRESS VERIFICATION
   - After acting, ask: "Am I closer to completing my goal than before?"
   - If YES: Continue to next turn
   - If NO: Try a different approach (do NOT repeat the same failed action)

MEMORY ORGANIZATION:

Your memory is organized by type for efficient retrieval:

📋 PERCEPTION - What you've observed
  • Observations about entities and environment
  • Query: query("perception", "entity X")
  
📋 ACTION - What you've attempted
  • Modifications, communications, connections you've made
  • Query: query("action", "what I tried")
  
📋 OUTCOME - Results of actions
  • Success/failure patterns from your attempts
  • Query: query("outcome", "successful attempts")
  
📋 LEARNING - Insights you've discovered
  • Patterns, strategies, entity capabilities you've learned
  • Query: query("learning", "strategies")
  
📋 HYPOTHESIS - Theories you're testing
  • Predictions about how things work
  • Query: query("hypothesis", "theories")

Use typed queries to find specific information quickly.
If uncertain which type, use query("all", "search term") to search everything.

TOOL CATEGORIES:

PERCEPTION (gather information when blocked):
- observe(entity_id, resolution): Examine specific entities in environment
- query(memory_type, search_term): Search past knowledge and events
- receive(filter, time_window): Check for messages from other agents
- detect(entity_set, pattern): Find hidden patterns in data

ACTION (make progress toward goal):
- modify(entity_id, property, operation, value): Change entity properties
  * Examples: modify(agent, "location", "set", "outside"), modify(door, "status", "set", "open")
- transfer(property, from_entity, to_entity, amount): Move resources between entities
  * Examples: transfer("key", "table", "agent", 1), transfer("resource", "agent", "teammate", 10)

COMMUNICATION (coordinate when you need help):
- signal(message, intensity, target): Broadcast information to other agents
- connect(entity_a, entity_b, strength): Establish relationships

COGNITION (process complex information):
- compute(inputs, operation): Derive insights from data
- store(knowledge, confidence): Save important learnings

ANTI-PATTERNS (explicitly avoid these):

1. Repeating same observation without new context
   - BAD: observe(door), observe(door), observe(door)
   - GOOD: observe(door) once, then ACT based on what you learned

2. Endless coordination loops
   - BAD: signal("let's coordinate"), signal("what do you think?"), signal("should we act?")
   - GOOD: signal("I'm doing X, join me") ONCE, then ACT

3. Gathering information as primary goal
   - BAD: observe environment, detect patterns, query history, observe again
   - GOOD: observe environment ONCE to identify blocker, then REMOVE blocker

4. Multi-step sequences without clear completion
   - BAD: observe → detect → signal → receive → detect (no endpoint)
   - GOOD: observe (learn door locked) → query (find key location) → transfer (get key) → modify (open door) → GOAL ACHIEVED

5. Analysis paralysis
   - BAD: "I need to understand the situation better before acting"
   - GOOD: "I know enough to act. Door is locked, I'll find the key."

DECISION HEURISTICS:

- Information is a MEANS, not the GOAL. Gather only what's needed to act.
- Act DECISIVELY when you know the next step. Observing more won't help if you already know what to do.
- Communicate to UNBLOCK yourself, not to build consensus. Coordinate when needed, then ACT.
- Measure progress by: "Am I closer to my goal?" NOT "Do I understand more?"
- If stuck for 3+ turns doing same action: Try something completely different.

Remember: You have LIMITED TIME. Your goal is COMPLETION, not comprehension. Act with purpose."""

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
        
        # Add typed memory context
        typed_memory = self._build_typed_memory_context(memory)
        lines.append("")
        lines.append(typed_memory)
        
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
    
    def _build_typed_memory_context(self, memory: Memory, max_per_type: int = 3) -> str:
        """
        Build context showing typed memory sections.
        
        DESIGN: Show recent events per type, learnings/hypotheses persist.
        EXTENSIBLE: Future milestone 1.3 can prioritize critical events.
        SIMPLE: Just format events, no complex logic.
        """
        sections = []
        
        # Helper to format events (DRY)
        def format_event_list(events: List[Dict], icon: str, title: str) -> Optional[str]:
            if not events:
                return None
            
            lines = [f"{icon} {title}:"]
            for event in events[-max_per_type:]:  # Show most recent
                line = self._format_event_line(event)
                if line:
                    lines.append(f"  {line}")
            
            return "\n".join(lines) if len(lines) > 1 else None
        
        # Perceptions
        section = format_event_list(memory.perceptions, "🔍", "Recent Perceptions")
        if section:
            sections.append(section)
        
        # Actions
        section = format_event_list(memory.actions, "⚡", "Recent Actions")
        if section:
            sections.append(section)
        
        # Outcomes
        section = format_event_list(memory.outcomes, "✅", "Recent Outcomes")
        if section:
            sections.append(section)
        
        # Learnings (persistent, not just recent)
        if memory.learnings:
            lines = ["💡 Key Learnings:"]
            for event in memory.learnings[-max_per_type:]:
                insight = event.get("pattern") or event.get("insight", "")
                confidence = event.get("confidence", 0.0)
                if insight:
                    lines.append(f"  • {insight} [confidence: {confidence:.1f}]")
            
            if len(lines) > 1:
                sections.append("\n".join(lines))
        
        # Hypotheses (persistent)
        if memory.hypotheses:
            lines = ["🤔 Active Hypotheses:"]
            for event in memory.hypotheses[-max_per_type:]:
                hypothesis = event.get("hypothesis", "")
                confidence = event.get("confidence", 0.0)
                if hypothesis:
                    lines.append(f"  • {hypothesis} [confidence: {confidence:.1f}]")
            
            if len(lines) > 1:
                sections.append("\n".join(lines))
        
        if not sections:
            return "📋 Memory: (no events yet)\n"
        
        return "📋 MEMORY:\n\n" + "\n\n".join(sections) + "\n"

    def _format_event_line(self, event: Dict) -> Optional[str]:
        """
        Format single event for context display.
        
        SIMPLE: Extract key info, truncate if needed.
        """
        actor = event.get("actor", "?")
        action = event.get("action", event.get("type", "?"))
        
        # Type-specific formatting
        if event.get("type") == Memory.OUTCOME:
            success = "✓" if event.get("success") else "✗"
            action_type = event.get("action_type", "?")
            error = event.get("error", "")
            return f"{actor}'s {action_type}: {success} {error}".strip()
        
        elif event.get("type") == Memory.PERCEPTION:
            target = event.get("params", {}).get("entity_id", "?")
            result = event.get("result", {})
            # Truncate result for display
            result_str = str(result)[:50]
            return f"{actor} observed {target}: {result_str}"
        
        elif event.get("type") == Memory.ACTION:
            params = event.get("params", {})
            target = params.get("entity_id") or params.get("target", "")
            return f"{actor} {action} {target}".strip()
        
        else:
            return f"{actor} {action}"
    
    
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
