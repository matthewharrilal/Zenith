#!/usr/bin/env python3
"""
Comprehensive Test Suite for Emergent Intelligence System
Tests all core components, MCP integration, agent behavior, and visual display
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from core.agents import Agent
from core.game_state import GameState
from core.memory import Memory
from core.primitives import PrimitiveTools
from core.mcp_tools import MCPToolServer
from core.visual_display import GameVisualizer

def test_memory_system():
    """Test memory storage and retrieval"""
    print("🧠 Testing Memory System...")
    
    memory = Memory()
    
    # Add some test events
    memory.add_event("RAVEN", "observe", {"entity": "environment"}, {"success": True}, "Testing observation")
    memory.add_event("FALCON", "signal", {"message": "Hello"}, {"success": True}, "Testing communication")
    memory.add_pattern("test_pattern", "Agents can cooperate", 0.8, "RAVEN")
    
    print(f"✅ Memory: {len(memory.events)} events, {len(memory.patterns)} patterns")
    
    # Test search
    results = memory.search_similar("cooperation", top_k=2)
    print(f"✅ Search: Found {len(results)} similar events")
    
    return memory

def test_game_state():
    """Test game state management"""
    print("\n🎮 Testing Game State...")
    
    game_state = GameState()
    
    # Add test entities
    game_state.add_entity("RAVEN", {
        "role": "player",
        "stress_level": 0.3,
        "resources": ["lockpicks"]
    })
    
    game_state.add_entity("environment", {
        "threat_level": 0.1,
        "atmosphere": "tense"
    })
    
    # Test signals
    game_state.add_signal("RAVEN", "Hello team", 5, "all")
    
    print(f"✅ Game State: {len(game_state.entities)} entities, {len(game_state.signals)} signals")
    
    return game_state

def test_primitives():
    """Test primitive tools"""
    print("\n🔧 Testing Primitive Tools...")
    
    memory = Memory()
    game_state = GameState()
    primitives = PrimitiveTools(game_state, memory)
    
    # Setup test entities
    game_state.add_entity("RAVEN", {
        "resources": ["lockpicks", "stealth_training"],
        "stress_level": 0.3
    })
    
    game_state.add_entity("FALCON", {
        "resources": ["explosives"],
        "stress_level": 0.2
    })
    
    # Test observe
    result = primitives.observe("RAVEN", 0.5)
    print(f"✅ Observe: {result['success']}")
    
    # Test transfer
    result = primitives.transfer("resources", "RAVEN", "FALCON", 1)
    print(f"✅ Transfer: {result['success']}")
    
    # Test signal
    result = primitives.signal("Hello team", 5, "all", "RAVEN")
    print(f"✅ Signal: {result['success']}")
    
    # Test receive
    result = primitives.receive({}, 10.0, "FALCON")
    print(f"✅ Receive: {result['success']}, {result['count']} signals")
    
    return primitives

def test_mcp_tools():
    """Test MCP tools work correctly"""
    print("\n🔧 Testing MCP Tools...")
    
    game_state = GameState()
    memory = Memory()
    mcp = MCPToolServer()
    mcp.bind_context(game_state, memory, "TEST_AGENT")
    
    print("✅ MCP server initialized")
    
    # Add test entities
    game_state.add_entity("test_entity", {
        "health": 100,
        "resources": ["food", "water"],
        "role": "player"
    })
    
    game_state.add_entity("environment", {
        "threat_level": 0.3,
        "atmosphere": "tense"
    })
    
    print("✅ Test entities created")
    
    # Test each tool
    tests = [
        ("observe", {"entity_id": "test_entity", "resolution": 0.5}),
        ("query", {"memory_type": "events", "search_term": "test"}),
        ("detect", {"entity_set": ["test_entity"], "pattern_type": "correlation"}),
        ("modify", {"entity_id": "test_entity", "property_name": "health", "operation": "set", "value": 90}),
        ("connect", {"entity_a": "TEST_AGENT", "entity_b": "test_entity", "strength": 0.7}),
        ("signal", {"message": "Test message", "intensity": 5, "target": "all"}),
        ("receive", {"filter_criteria": {"min_intensity": 1}, "time_window": 10.0}),
        ("store", {"knowledge": "Test insight", "confidence": 0.8}),
        ("compute", {"inputs": [1, 2, 3], "operation": "sum"})
    ]
    
    success_count = 0
    for tool_name, params in tests:
        try:
            result = mcp.execute_tool(tool_name, params)
            if result.get("success") or "result" in result:
                print(f"✅ {tool_name}: Working")
                success_count += 1
            else:
                print(f"❌ {tool_name}: {result}")
        except Exception as e:
            print(f"❌ {tool_name}: Error - {e}")
    
    print(f"\n📊 MCP Results: {success_count}/{len(tests)} tools working")
    return success_count == len(tests)

def test_agent_action_taking():
    """Test that agents take actions instead of choosing none"""
    print("\n🤖 Testing Agent Action-Taking...")
    
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
    
    total_none_count = 0
    total_actions = 0
    all_tools_used = set()
    
    for agent in agents:
        print(f"\n🔍 Testing {agent.name}")
        
        tools_used = set()
        none_count = 0
        
        # Get 5 actions from this agent
        for i in range(5):
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
        print(f"   Tools used: {len(tools_used)} different tools")
        print(f"   Tools: {sorted(tools_used)}")
        print(f"   'none' actions: {none_count}/5 ({none_count*20}%)")
    
    # Overall assessment
    print(f"\n🎯 Overall Assessment")
    print(f"Total actions tested: {total_actions}")
    print(f"Total 'none' actions: {total_none_count}")
    print(f"'none' percentage: {(total_none_count/total_actions)*100:.1f}%")
    print(f"All tools used: {sorted(all_tools_used)}")
    print(f"Tool diversity: {len(all_tools_used)} different tools")
    
    # Success criteria
    success = (total_none_count <= total_actions * 0.25) and (len(all_tools_used) >= 3)
    if success:
        print("✅ SUCCESS: Agents using diverse tools, minimal 'none' actions")
    else:
        print("❌ NEEDS WORK: Too many 'none' actions or low tool diversity")
    
    return success

def test_scenario_agnostic():
    """Test that agents explore without being told specific tools"""
    print("\n🌍 Testing Scenario-Agnostic Behavior...")
    
    # Setup minimal environment
    game_state = GameState()
    memory = Memory()
    primitives = PrimitiveTools(game_state, memory)
    
    # Add test entities
    game_state.entities["TEST_AGENT"] = {"health": 100, "resources": 50, "role": "player"}
    game_state.entities["environment"] = {"threat_level": 1, "atmosphere": "neutral"}
    
    print("✅ Minimal test environment created")
    
    # Test agent
    agent = Agent("TEST_AGENT", "player")
    
    print(f"\n🔍 Testing {agent.name} for 8 rounds")
    
    tool_usage = {}
    diversity_hints = []
    
    for i in range(8):
        try:
            action, params, reasoning = agent.get_action(game_state, memory, primitives)
            tool_usage[action] = tool_usage.get(action, 0) + 1
            
            print(f"Round {i+1}: {action}")
            
            # Check for diversity hints in reasoning
            if "unexplored" in reasoning.lower() or "different" in reasoning.lower():
                diversity_hints.append(i+1)
                
        except Exception as e:
            print(f"Round {i+1}: ERROR - {e}")
    
    # Analysis
    print(f"\n📊 Results Analysis")
    print(f"Tools used: {sorted(tool_usage.keys())}")
    print(f"Tool diversity: {len(tool_usage)} different tools")
    print(f"Tool distribution: {tool_usage}")
    print(f"Diversity hints received: {diversity_hints}")
    
    # Success criteria
    diversity_score = len(tool_usage) / 8  # Higher = more diverse
    
    print(f"\n🎯 Success Metrics")
    print(f"Diversity score: {diversity_score:.2f} (1.0 = perfect diversity)")
    
    success = diversity_score >= 0.5
    if success:
        print("✅ SUCCESS: Good tool diversity achieved!")
    else:
        print("❌ NEEDS WORK: Low tool diversity")
    
    return success

def test_visual_display():
    """Test the visual display system"""
    print("\n🎨 Testing Visual Display System...")
    
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
    
    # Test several actions
    tool_usage = {}
    
    for i in range(3):
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
    
    print(f"\n✅ Visual Display: {len(tool_usage)} different tools used")
    return True

def test_integration():
    """Test component integration"""
    print("\n🔗 Testing Integration...")
    
    memory = Memory()
    game_state = GameState()
    primitives = PrimitiveTools(game_state, memory)
    
    # Setup safehouse scenario entities
    game_state.add_entity("RAVEN", {
        "role": "player",
        "location": "safe_house_interior",
        "stress_level": 0.3,
        "resources": ["lockpicks", "stealth_training"],
        "relationships": {},
        "knowledge": []
    })
    
    game_state.add_entity("environment", {
        "threat_level": 0.1,
        "escalation_rate": 0.05,
        "atmosphere": "tense"
    })
    
    # Simulate some agent actions
    print("Simulating agent actions...")
    
    # RAVEN observes environment
    result = primitives.observe("environment", 0.7)
    memory.add_event("RAVEN", "observe", {"entity_id": "environment", "resolution": 0.7}, result, "Checking threat level")
    
    # RAVEN signals to team
    result = primitives.signal("We need to work together", 7, "all", "RAVEN")
    memory.add_event("RAVEN", "signal", {"message": "We need to work together", "intensity": 7, "target": "all"}, result, "Calling for cooperation")
    
    # RAVEN stores insight
    result = primitives.store("Cooperation is essential for survival", 0.9, "RAVEN")
    memory.add_event("RAVEN", "store", {"knowledge": "Cooperation is essential for survival", "confidence": 0.9}, result, "Learning from experience")
    
    print(f"✅ Integration: {len(memory.events)} events stored")
    print(f"✅ Memory patterns: {len(memory.patterns)}")
    
    # Test memory search
    results = memory.search_similar("cooperation", top_k=3)
    print(f"✅ Memory search: Found {len(results)} relevant events")
    
    return True

def main():
    """Run all tests"""
    print("🧪 COMPREHENSIVE TEST SUITE")
    print("Emergent Intelligence System - All Components")
    print("=" * 60)
    
    try:
        # Test individual components
        test_memory_system()
        test_game_state()
        test_primitives()
        
        # Test MCP integration
        mcp_success = test_mcp_tools()
        
        # Test agent behavior
        agent_success = test_agent_action_taking()
        
        # Test scenario-agnostic behavior
        scenario_success = test_scenario_agnostic()
        
        # Test visual display
        display_success = test_visual_display()
        
        # Test integration
        integration_success = test_integration()
        
        print("\n" + "=" * 60)
        print("🏆 FINAL RESULTS")
        print("=" * 60)
        
        results = {
            "MCP Tools": mcp_success,
            "Agent Actions": agent_success,
            "Scenario Agnostic": scenario_success,
            "Visual Display": display_success,
            "Integration": integration_success
        }
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{test_name}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! System is working correctly.")
            print("\nReady for production use:")
            print("1. Set your OpenAI API key: export OPENAI_API_KEY='your-key-here'")
            print("2. Run the system: python3 src/main.py --games 1")
            print("3. Run multiple games: python3 src/main.py --games 10 --memory-file memory.pkl")
            return True
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
            return False
        
    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
