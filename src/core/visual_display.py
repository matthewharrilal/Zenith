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
        """Display round with balanced information"""
        self.round = round_num
        
        # Clean header with timestamp
        print(f"\n═══ Round {round_num} ═══ [{timestamp:.1f}s]")
        
        # Three-column layout: Actions | Memory | Dynamics
        self._display_main_panel(agents_data, game_state)
        
        # Highlight key events only
        self._display_key_events(agents_data)
        
    def _display_main_panel(self, agents_data: List[Dict], game_state):
        """Main information panel with clean layout"""
        
        # Column 1: Agent Actions (simplified)
        print("\n│ ACTIONS          │ MEMORY/PATTERNS     │ STATE")
        print("├──────────────────┼────────────────────┼──────────────")
        
        for agent in agents_data:
            name = agent['name']
            action = agent['action']
            params = agent.get('params', {})
            
            # Track tool usage
            self.tool_usage[name].append(action)
            
            # Format action display
            action_str = self._format_action(action, params)
            
            # Check for memory queries
            memory_str = self._format_memory(action, params)
            
            # Get agent state
            agent_entity = game_state.get_entity(name)
            state_str = self._format_state(agent_entity)
            
            # Display in columns
            print(f"│ {name:6} {action_str:9} │ {memory_str:18} │ {state_str}")
        
        print("└──────────────────┴────────────────────┴──────────────")
    
    def _format_action(self, action: str, params: Dict) -> str:
        """Format action concisely"""
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
        
        # Add target for context-dependent actions
        if action == 'observe':
            target = params.get('entity_id', '')[:3]
            return f"{icon} {target}"
        elif action == 'signal':
            target = params.get('target', 'all')[:3]
            return f"{icon}→{target}"
        else:
            return f"{icon} {action[:6]}"
    
    def _format_memory(self, action: str, params: Dict) -> str:
        """Format memory queries and patterns"""
        if action == 'query':
            mem_type = params.get('memory_type', '?')[:3]
            search = params.get('search_term', '?')[:10]
            return f"🔍{mem_type}:{search}"
        elif action == 'store':
            conf = params.get('confidence', 0)
            return f"💾 conf:{conf:.1f}"
        else:
            return ""
    
    def _format_state(self, agent_entity: Optional[Dict]) -> str:
        """Format agent state compactly"""
        if not agent_entity:
            return "?"
        
        health = agent_entity.get('health', 100)
        resources = agent_entity.get('resources', 0)
        
        # Handle resources as list or number
        if isinstance(resources, list):
            resource_count = len(resources)
        else:
            resource_count = resources
        
        # Use indicators for changes
        h_bar = "█" * (health // 20)  # 5-bar health
        r_sym = "↑" if resource_count > 60 else "↓" if resource_count < 30 else "→"
        
        return f"H:{h_bar:5} R:{resource_count:02d}{r_sym}"
    
    def _display_key_events(self, agents_data: List[Dict]):
        """Show only significant events"""
        events = []
        
        for agent in agents_data:
            action = agent['action']
            name = agent['name']
            
            # Track significant actions
            if action == 'transfer':
                to = agent['params'].get('to_entity', '?')
                prop = agent['params'].get('property_name', '?')
                events.append(f"{name}→{to}: shared {prop}")
            
            elif action == 'connect':
                other = agent['params'].get('entity_b', '?')
                strength = agent['params'].get('strength', 0)
                if abs(strength) > 0.5:
                    rel = "allied" if strength > 0 else "opposed"
                    events.append(f"{name} {rel} with {other}")
            
            elif action == 'signal':
                msg = agent['params'].get('message', '')
                if any(word in msg.lower() for word in ['cooperat', 'ally', 'help', 'attack']):
                    events.append(f"{name}: \"{msg[:25]}...\"")
        
        if events:
            print("\n» Key Events:", " | ".join(events[:2]))  # Max 2 events
    
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
