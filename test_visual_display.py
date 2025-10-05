#!/usr/bin/env python3
"""
Test Visual Display System
Demonstrates clean visual output for game events
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from core.agents import Agent
from core.game_state import GameState
from core.memory import Memory
from core.primitives import PrimitiveTools
from core.visual_display import GameVisualizer

def test_visual_display():
    """Test the visual display system"""
    print("🎨 Testing Visual Display System")
    print("=" * 60)
    
    # Setup
    game_state = GameState()
    memory = Memory()
    primitives = PrimitiveTools(game_state, memory)
    visualizer = GameVisualizer()
    
    # Add test entities
    game_state.entities["FALCON"] = {"health": 100, "resources": 50, "role": "player"}
    game_state.entities["RAVEN"] = {"health": 85, "resources": 30, "role": "player"}
    game_state.entities["environment"] = {
        "threat_level": 2, 
        "atmosphere": "tense",
        "power_remaining": 3.0
    }
    
    # Add some signals
    game_state.add_signal("RAVEN", "Hello everyone! Let's work together.", 5, "all")
    game_state.add_signal("FALCON", "I agree, cooperation is key.", 4, "all")
    
    # Test agent
    agent = Agent("FALCON", "player")
    
    # Display round header
    visualizer.display_round_header(1, game_state.timestamp)
    
    # Display game state
    visualizer.display_game_state(game_state)
    
    # Test several actions
    tool_usage = {}
    
    for i in range(5):
        print(f"\n--- Action {i+1} ---")
        
        # Get action
        action, params, reasoning = agent.get_action(game_state, memory, primitives)
        tool_usage[action] = tool_usage.get(action, 0) + 1
        
        # Display action
        visualizer.display_agent_action(agent.name, action, params, reasoning)
        
        # Simulate action result
        if action != "none":
            result = {"success": True, "message": "Action completed"}
        else:
            result = {"success": False, "error": "No action taken"}
        
        visualizer.display_action_result(result)
    
    # Display signals
    signals = game_state.get_recent_signals(10.0)
    visualizer.display_signals(signals)
    
    # Display tool diversity
    visualizer.display_tool_diversity(tool_usage)
    
    # Display round summary
    events = [
        f"{agent.name} used {len(tool_usage)} different tools",
        f"Total actions: {sum(tool_usage.values())}",
        f"Most used tool: {max(tool_usage.items(), key=lambda x: x[1])[0]}"
    ]
    visualizer.display_round_summary(events)

if __name__ == "__main__":
    test_visual_display()
