"""
Visual Display Module - Balanced visual output for simulation events
"""

from typing import Dict, List, Optional
from collections import defaultdict, deque

class SimulationDisplay:
    """Balanced visual output - informative but not overwhelming"""
    
    def __init__(self):
        self.round = 0
        self.tool_usage = defaultdict(lambda: deque(maxlen=5))  # Last 5 tools per agent
        self.key_events = []
        
    def display_round(self, round_num: int, timestamp: float, agents_data: List[Dict], game_state):
        """Display round with clean, informative layout"""
        self.round = round_num
        
        # Clean header
        print(f"\n═══ Round {round_num} ═══ [{timestamp:.1f}s]")
        
        # Main action panel
        self._display_actions(agents_data, game_state)
        
        # Show key events if any
        self._display_key_events(agents_data)
        
    def _display_actions(self, agents_data: List[Dict], game_state):
        """Display agent actions in clean format"""
        
        print("\n│ AGENT   │ ACTION        │ TARGET/INFO")
        print("├─────────┼───────────────┼─────────────────")
        
        for agent in agents_data:
            name = agent['name']
            action = agent['action']
            params = agent.get('params', {})
            
            # Track tool usage
            self.tool_usage[name].append(action)
            
            # Format action display
            action_str = self._format_action(action, params)
            target_str = self._format_target(action, params)
            
            # Display in clean format
            print(f"│ {name:7} │ {action_str:13} │ {target_str}")
        
        print("└─────────┴───────────────┴─────────────────")
    
    def _format_action(self, action: str, params: Dict) -> str:
        """Format action with icon"""
        icons = {
            'observe': '👁',
            'signal': '💬',
            'query': '🔍',
            'transfer': '↔',
            'connect': '🔗',
            'detect': '🎯',
            'modify': '🔧',
            'store': '💾',
            'compute': '🧮',
            'none': '⏸'
        }
        
        icon = icons.get(action, '•')
        return f"{icon} {action}"
    
    def _format_target(self, action: str, params: Dict) -> str:
        """Format target information"""
        if action == 'observe':
            target = params.get('entity_id', 'unknown')
            return f"→ {target}"
        elif action == 'signal':
            target = params.get('target', 'all')
            message = params.get('message', '')[:20]
            return f"→ {target}: {message}..."
        elif action == 'query':
            mem_type = params.get('memory_type', 'events')
            search = params.get('search_term', '')[:15]
            return f"→ {mem_type}: {search}..."
        elif action == 'receive':
            time_window = params.get('time_window', 10.0)
            return f"→ last {time_window:.0f}s"
        else:
            return f"→ {action}"
    
    
    def _display_key_events(self, agents_data: List[Dict]):
        """Show significant events"""
        events = []
        
        for agent in agents_data:
            action = agent['action']
            name = agent['name']
            params = agent.get('params', {})
            
            # Track significant actions
            if action == 'transfer':
                to = params.get('to_entity', '?')
                prop = params.get('property_name', '?')
                events.append(f"{name}→{to}: shared {prop}")
            
            elif action == 'connect':
                other = params.get('entity_b', '?')
                strength = params.get('strength', 0)
                if abs(strength) > 0.5:
                    rel = "allied" if strength > 0 else "opposed"
                    events.append(f"{name} {rel} with {other}")
            
            elif action == 'signal':
                msg = params.get('message', '')
                if any(word in msg.lower() for word in ['cooperat', 'ally', 'help', 'attack', 'escape']):
                    events.append(f"{name}: \"{msg[:30]}...\"")
        
        if events:
            print(f"\n» Key Events: {' | '.join(events[:2])}")
    
    def display_pattern_insight(self, every_n_rounds=5):
        """Show pattern insights periodically"""
        if self.round % every_n_rounds != 0:
            return
        
        print("\n▼ Pattern Insight ▼")
        
        for agent, tools in self.tool_usage.items():
            if len(tools) >= 3:
                # Convert deque to list for slicing
                tools_list = list(tools)
                
                # Detect patterns
                unique = len(set(tools_list))
                if unique == 1:
                    print(f"  {agent}: Stuck in {tools_list[0]} loop")
                elif unique >= 4:
                    print(f"  {agent}: Exploring (high diversity)")
                
                # Detect sequences
                if len(tools_list) >= 3:
                    if tools_list[-3:] == ['observe', 'signal', 'connect']:
                        print(f"  {agent}: Building alliance pattern")
                    elif tools_list[-2:] == ['query', 'store']:
                        print(f"  {agent}: Learning pattern")

# Legacy compatibility
class GameVisualizer(SimulationDisplay):
    """Legacy compatibility wrapper"""
    def __init__(self):
        super().__init__()
        self.round_number = 0
    
    def display_round_header(self, round_num: int, timestamp: float):
        """Legacy method - redirect to new display"""
        self.round_number = round_num
        print(f"\n═══ Round {round_num} ═══ [{timestamp:.1f}s]")
    
    def display_agent_action(self, agent_name: str, action: str, params: Dict, reasoning: str):
        """Legacy method - simplified display"""
        action_str = self._format_action(action, params)
        print(f"  {agent_name}: {action_str}")
    
    def display_action_result(self, result: Dict):
        """Legacy method - simple result display"""
        if result.get('success'):
            print(f"    ✅ Success")
        else:
            error = result.get('error', 'Unknown error')
            print(f"    ❌ Failed: {error}")
