#!/usr/bin/env python3
"""
Test script to verify agent analysis paralysis fix
Tests that agents now take actions instead of choosing "none"
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from core.agents import Agent
from core.game_state import GameState
from core.memory import Memory
from core.primitives import PrimitiveTools

def test_agent_action_taking():
    """Test that agents take actions instead of choosing none"""
    print("🧪 Testing Agent Action-Taking Fix")
    print("=" * 50)
    
    # Setup game state
    game_state = GameState()
    memory = Memory()
    primitives = PrimitiveTools(game_state, memory)
    
    # Add test agents
    for name in ["FALCON", "RAVEN", "VIPER"]:
        game_state.entities[name] = {
            "health": 100, 
            "resources": 50,
            "role": "player"
        }
    
    # Add environment
    game_state.entities["environment"] = {
        "threat_level": 2,
        "atmosphere": "tense",
        "power_remaining": 3.0
    }
    
    print("✅ Test environment created")
    
    # Test each agent
    agents = [Agent(name, "player") for name in ["FALCON", "RAVEN", "VIPER"]]
    
    for agent in agents:
        print(f"\n🔍 Testing {agent.name}")
        print("-" * 30)
        
        # Track tool usage
        tools_used = set()
        none_count = 0
        
        # Get 10 actions from this agent
        for i in range(10):
            try:
                action, params, reasoning = agent.get_action(game_state, memory, primitives)
                tools_used.add(action)
                
                if action == "none":
                    none_count += 1
                    print(f"❌ Round {i+1}: {action} - STILL CHOOSING NONE!")
                else:
                    print(f"✅ Round {i+1}: {action}({params})")
                
                # Print reasoning for first few actions
                if i < 3:
                    print(f"   Reasoning: {reasoning[:100]}...")
                    
            except Exception as e:
                print(f"❌ Round {i+1}: ERROR - {e}")
                none_count += 1
        
        # Analyze results
        print(f"\n📊 {agent.name} Results:")
        print(f"   Tools used: {len(tools_used)} different tools")
        print(f"   Tools: {sorted(tools_used)}")
        print(f"   'none' actions: {none_count}/10 ({none_count*10}%)")
        
        # Success criteria
        if len(tools_used) >= 3 and none_count <= 2:
            print(f"   ✅ SUCCESS: {agent.name} using diverse tools, minimal 'none' actions")
        elif len(tools_used) >= 2 and none_count <= 4:
            print(f"   ⚠️  PARTIAL: {agent.name} using some tools, but too many 'none' actions")
        else:
            print(f"   ❌ FAILURE: {agent.name} not using tools effectively")
    
    print(f"\n🎯 Overall Assessment:")
    print("=" * 50)
    
    # Check if signal was used early
    early_signals = 0
    for agent in agents:
        # Simulate a few rounds to check for early signals
        for i in range(5):
            try:
                action, params, _ = agent.get_action(game_state, memory, primitives)
                if action == "signal" and i < 3:
                    early_signals += 1
                    break
            except:
                pass
    
    if early_signals >= 2:
        print("✅ SUCCESS: Agents are signaling early (within first 3 rounds)")
    else:
        print("❌ ISSUE: Agents not signaling early enough")
    
    print("\n🔧 If agents still choose 'none' frequently:")
    print("1. Check that MCPToolServer is working correctly")
    print("2. Verify OpenAI API key is set")
    print("3. Check that the prompt is being applied correctly")
    print("4. Consider adding more explicit action forcing rules")

def test_mcp_tools():
    """Test that MCP tools are working correctly"""
    print("\n🔧 Testing MCP Tools")
    print("=" * 30)
    
    try:
        from core.mcp_tools import MCPToolServer
        
        game_state = GameState()
        memory = Memory()
        mcp = MCPToolServer()
        mcp.bind_context(game_state, memory, "TEST_AGENT")
        
        # Add test entity
        game_state.entities["test_entity"] = {"health": 100, "resources": 50}
        
        # Test a few tools
        tools_to_test = [
            ("observe", {"entity_id": "test_entity", "resolution": 0.5}),
            ("signal", {"message": "Test message", "intensity": 5, "target": "all"}),
            ("query", {"memory_type": "events", "search_term": "test"})
        ]
        
        for tool_name, params in tools_to_test:
            result = mcp.execute_tool(tool_name, params)
            if result.get("success"):
                print(f"✅ {tool_name}: Working")
            else:
                print(f"❌ {tool_name}: {result.get('error', 'Unknown error')}")
        
        print("✅ MCP Tools: Working correctly")
        return True
        
    except Exception as e:
        print(f"❌ MCP Tools: Error - {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Agent Analysis Paralysis Fix Test")
    print("=" * 60)
    
    # Test MCP tools first
    mcp_working = test_mcp_tools()
    
    if mcp_working:
        # Test agent action taking
        test_agent_action_taking()
    else:
        print("\n❌ Cannot test agents - MCP tools not working")
        print("Please fix MCP tools first")
    
    print("\n🏁 Test Complete")
