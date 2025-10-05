#!/usr/bin/env python3
"""
Quick test to verify agent action-taking improvements
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from core.agents import Agent
from core.game_state import GameState
from core.memory import Memory
from core.primitives import PrimitiveTools

def quick_test():
    """Quick test of agent action-taking"""
    print("🚀 Quick Agent Action Test")
    print("=" * 40)
    
    # Setup
    game_state = GameState()
    memory = Memory()
    primitives = PrimitiveTools(game_state, memory)
    
    # Add test entities
    game_state.entities["FALCON"] = {"health": 100, "resources": 50, "role": "player"}
    game_state.entities["RAVEN"] = {"health": 100, "resources": 50, "role": "player"}
    game_state.entities["environment"] = {"threat_level": 2, "atmosphere": "tense"}
    
    # Test one agent
    agent = Agent("FALCON", "player")
    
    print("Testing FALCON for 5 rounds:")
    tools_used = set()
    
    for i in range(5):
        try:
            action, params, reasoning = agent.get_action(game_state, memory, primitives)
            tools_used.add(action)
            print(f"Round {i+1}: {action} - {params}")
        except Exception as e:
            print(f"Round {i+1}: ERROR - {e}")
    
    print(f"\nTools used: {sorted(tools_used)}")
    print(f"Tool diversity: {len(tools_used)} different tools")
    
    if len(tools_used) >= 3:
        print("✅ SUCCESS: Good tool diversity!")
    elif len(tools_used) >= 2:
        print("⚠️  PARTIAL: Some tool diversity")
    else:
        print("❌ ISSUE: Limited tool usage")

if __name__ == "__main__":
    quick_test()
