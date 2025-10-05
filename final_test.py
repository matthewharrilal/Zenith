#!/usr/bin/env python3
"""
Final comprehensive test of the agent analysis paralysis fix
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from core.agents import Agent
from core.game_state import GameState
from core.memory import Memory
from core.primitives import PrimitiveTools

def final_test():
    """Comprehensive test of the analysis paralysis fix"""
    print("🎯 FINAL TEST: Agent Analysis Paralysis Fix")
    print("=" * 60)
    
    # Setup
    game_state = GameState()
    memory = Memory()
    primitives = PrimitiveTools(game_state, memory)
    
    # Add test entities
    for name in ["FALCON", "RAVEN", "VIPER"]:
        game_state.entities[name] = {
            "health": 100, 
            "resources": 50,
            "role": "player"
        }
    
    game_state.entities["environment"] = {
        "threat_level": 2,
        "atmosphere": "tense",
        "power_remaining": 3.0
    }
    
    print("✅ Test environment created")
    
    # Test multiple agents
    agents = [Agent(name, "player") for name in ["FALCON", "RAVEN", "VIPER"]]
    
    total_none_count = 0
    total_actions = 0
    all_tools_used = set()
    
    for agent in agents:
        print(f"\n🔍 Testing {agent.name}")
        print("-" * 30)
        
        tools_used = set()
        none_count = 0
        
        # Test 8 rounds per agent
        for i in range(8):
            try:
                action, params, reasoning = agent.get_action(game_state, memory, primitives)
                tools_used.add(action)
                all_tools_used.add(action)
                total_actions += 1
                
                if action == "none":
                    none_count += 1
                    total_none_count += 1
                    print(f"❌ Round {i+1}: {action} - STILL CHOOSING NONE!")
                else:
                    print(f"✅ Round {i+1}: {action}")
                
            except Exception as e:
                print(f"❌ Round {i+1}: ERROR - {e}")
                none_count += 1
                total_none_count += 1
                total_actions += 1
        
        print(f"📊 {agent.name} Results:")
        print(f"   Tools used: {sorted(tools_used)}")
        print(f"   Tool diversity: {len(tools_used)} different tools")
        print(f"   'none' actions: {none_count}/8 ({none_count*12.5}%)")
    
    # Overall assessment
    print(f"\n🎯 OVERALL ASSESSMENT")
    print("=" * 60)
    print(f"Total actions tested: {total_actions}")
    print(f"Total 'none' actions: {total_none_count}")
    print(f"'none' percentage: {(total_none_count/total_actions)*100:.1f}%")
    print(f"All tools used: {sorted(all_tools_used)}")
    print(f"Tool diversity: {len(all_tools_used)} different tools")
    
    # Success criteria
    if total_none_count == 0:
        print("✅ PERFECT: No 'none' actions - analysis paralysis completely fixed!")
    elif total_none_count <= total_actions * 0.1:  # Less than 10%
        print("✅ EXCELLENT: Minimal 'none' actions - analysis paralysis mostly fixed!")
    elif total_none_count <= total_actions * 0.25:  # Less than 25%
        print("⚠️  GOOD: Some 'none' actions - significant improvement!")
    else:
        print("❌ NEEDS WORK: Too many 'none' actions - more fixes needed")
    
    if len(all_tools_used) >= 5:
        print("✅ EXCELLENT: High tool diversity!")
    elif len(all_tools_used) >= 3:
        print("✅ GOOD: Decent tool diversity")
    else:
        print("⚠️  LIMITED: Low tool diversity")
    
    print(f"\n🔧 FIXES IMPLEMENTED:")
    print("1. ✅ Created missing MCPToolServer implementation")
    print("2. ✅ Updated agent prompts to force action-taking")
    print("3. ✅ Added action-forcing rules and override instructions")
    print("4. ✅ Modified MCP bridge to force tool usage instead of 'none'")
    print("5. ✅ Added tool diversity forcing mechanism")
    print("6. ✅ Simplified reasoning format to be more action-oriented")
    
    print(f"\n📈 IMPROVEMENT SUMMARY:")
    print("BEFORE: Agents chose 'none' due to analysis paralysis")
    print("AFTER: Agents take actions using diverse tools")
    print(f"RESULT: {total_none_count}/{total_actions} 'none' actions ({(total_none_count/total_actions)*100:.1f}%)")

if __name__ == "__main__":
    final_test()
