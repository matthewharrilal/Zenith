"""
Simple Visual Display for simulation events
"""

from typing import Dict, List

class SimulationDisplay:
    """Simple visual output for simulation events"""
    
    def __init__(self):
        self.round = 0
        
    def display_round(self, round_num: int, timestamp: float, agents_data: List[Dict], game_state):
        """Display round with simple format"""
        self.round = round_num
        print(f"\n--- Round {round_num} [{timestamp:.1f}s] ---")
        
        for agent in agents_data:
            name = agent['name']
            actions = agent.get('actions', [])
            
            if actions:
                for action_data in actions:
                    action = action_data['action']
                    params = action_data.get('params', {})
                    print(f"  {name}: {action}({self._format_params(params)})")
            else:
                print(f"  {name}: No actions")
    
    def _format_params(self, params: Dict) -> str:
        """Format parameters for display"""
        if not params:
            return ""
        
        # Show key parameters only
        key_params = []
        for key, value in params.items():
            if key in ['entity_id', 'target', 'message', 'memory_type']:
                if isinstance(value, str) and len(value) > 20:
                    value = value[:20] + "..."
                key_params.append(f"{key}={value}")
        
        return ", ".join(key_params[:2])  # Max 2 params
    
    def display_pattern_insight(self):
        """Placeholder for pattern insights"""
        pass