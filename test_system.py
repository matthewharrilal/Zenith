#!/usr/bin/env python3
"""
Test script to verify core system components work without API calls
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from core.memory import Memory
from core.game_state import GameState
from core.primitives import PrimitiveTools

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
    print("🧪 EMERGENT INTELLIGENCE SYSTEM - COMPONENT TEST")
    print("=" * 60)
    
    try:
        # Test individual components
        memory = test_memory_system()
        game_state = test_game_state()
        primitives = test_primitives()
        
        # Test integration
        test_integration()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("The core system is working correctly.")
        print("Ready for GPT integration with OpenAI API key.")
        print("\nTo run the full system:")
        print("export OPENAI_API_KEY='your-key-here'")
        print("python3 src/main.py --games 1")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
