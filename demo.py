#!/usr/bin/env python3
"""
Demo script showing the Emergent Intelligence System in action
This demonstrates the core concepts without requiring an API key
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from core.memory import Memory
from core.game_state import GameState
from core.primitives import PrimitiveTools

def demo_emergence():
    """Demonstrate how emergence works through primitive tool interactions"""
    
    print("🧠 EMERGENT INTELLIGENCE SYSTEM DEMO")
    print("=" * 60)
    print("This demo shows how complex behaviors emerge from simple tools")
    print("=" * 60)
    
    # Initialize system
    memory = Memory()
    game_state = GameState()
    primitives = PrimitiveTools(game_state, memory)
    
    # Setup safehouse scenario
    print("\n🏠 Setting up Safe House scenario...")
    
    # Add agents
    game_state.add_entity("RAVEN", {
        "role": "player",
        "location": "safe_house_interior",
        "stress_level": 0.3,
        "resources": ["lockpicks", "stealth_training"],
        "relationships": {},
        "knowledge": []
    })
    
    game_state.add_entity("FALCON", {
        "role": "player",
        "location": "safe_house_interior", 
        "stress_level": 0.2,
        "resources": ["explosives", "technical_skills"],
        "relationships": {},
        "knowledge": []
    })
    
    game_state.add_entity("VIPER", {
        "role": "player",
        "location": "safe_house_interior",
        "stress_level": 0.4,
        "resources": ["vehicle_access", "combat_training"],
        "relationships": {},
        "knowledge": []
    })
    
    # Add environment
    game_state.add_entity("environment", {
        "threat_level": 0.1,
        "escalation_rate": 0.05,
        "atmosphere": "tense"
    })
    
    game_state.add_entity("exit_door", {
        "barrier_strength": 100,
        "complexity": 85,
        "requires_cooperation": True
    })
    
    print("✅ Scenario initialized with 3 agents in compromised safe house")
    
    # Simulate emergent behaviors
    print("\n🎭 Simulating emergent agent behaviors...")
    print("-" * 40)
    
    # Game 1: Initial discovery and basic cooperation
    print("\n🎮 GAME 1: Discovery Phase")
    simulate_agent_actions(primitives, memory, game_state, 1)
    
    # Game 2: Learning from memory and developing strategies
    print("\n🎮 GAME 2: Strategy Development")
    simulate_agent_actions(primitives, memory, game_state, 2)
    
    # Game 3: Complex social dynamics emerge
    print("\n🎮 GAME 3: Social Dynamics")
    simulate_agent_actions(primitives, memory, game_state, 3)
    
    # Analyze emergence
    print("\n🔬 EMERGENCE ANALYSIS")
    print("-" * 40)
    analyze_emergence(memory, game_state)
    
    print("\n" + "=" * 60)
    print("🎯 DEMO COMPLETE!")
    print("This shows how simple tools can lead to complex behaviors.")
    print("With GPT integration, agents would develop even more sophisticated strategies.")
    print("=" * 60)

def simulate_agent_actions(primitives, memory, game_state, game_num):
    """Simulate agent actions for a single game"""
    
    actions = [
        # RAVEN actions
        ("RAVEN", "observe", {"entity_id": "environment", "resolution": 0.7}, "Assessing threat level"),
        ("RAVEN", "signal", {"message": "We need to work together", "intensity": 7, "target": "all", "sender": "RAVEN"}, "Calling for cooperation"),
        ("RAVEN", "observe", {"entity_id": "exit_door", "resolution": 0.5}, "Examining exit options"),
        
        # FALCON actions  
        ("FALCON", "receive", {"filter_criteria": {}, "time_window": 10.0, "receiver": "FALCON"}, "Listening for communications"),
        ("FALCON", "signal", {"message": "I have explosives, can help with door", "intensity": 6, "target": "RAVEN", "sender": "FALCON"}, "Offering resources"),
        ("FALCON", "connect", {"entity_a": "FALCON", "entity_b": "RAVEN", "strength": 0.3}, "Building trust"),
        
        # VIPER actions
        ("VIPER", "observe", {"entity_id": "FALCON", "resolution": 0.6}, "Assessing FALCON's capabilities"),
        ("VIPER", "transfer", {"property_name": "resources", "from_entity": "VIPER", "to_entity": "FALCON", "amount": 1}, "Sharing vehicle access"),
        ("VIPER", "store", {"knowledge": "FALCON is trustworthy and has explosives", "confidence": 0.8, "discoverer": "VIPER"}, "Learning about allies"),
    ]
    
    for i, (actor, action, params, reasoning) in enumerate(actions):
        print(f"  [{i+1}] {actor}: {action}")
        
        # Execute action
        try:
            result = getattr(primitives, action)(**params)
            
            # Store in memory
            memory.add_event(actor, action, params, result, reasoning)
            
            # Show result
            if result.get('success'):
                if 'observations' in result:
                    print(f"      📊 Observed: {result['observations']}")
                elif 'transferred' in result:
                    print(f"      🔄 Transferred: {result['transferred']}")
                elif 'signals' in result:
                    print(f"      📡 Received {len(result['signals'])} signals")
                elif 'stored_knowledge' in result:
                    print(f"      💾 Stored: {result['stored_knowledge']}")
            else:
                print(f"      ❌ Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"      ❌ Error: {e}")
    
    # Update game state
    game_state.timestamp += 10.0
    
    # Show memory growth
    print(f"  📚 Memory: {len(memory.events)} events, {len(memory.patterns)} patterns")

def analyze_emergence(memory, game_state):
    """Analyze emergent patterns in the simulation"""
    
    # Count different types of events
    cooperation_events = len([e for e in memory.events if e['action'] == 'transfer'])
    communication_events = len([e for e in memory.events if e['action'] == 'signal'])
    observation_events = len([e for e in memory.events if e['action'] == 'observe'])
    learning_events = len([e for e in memory.events if e['action'] == 'store'])
    
    print(f"📊 Event Analysis:")
    print(f"   Cooperation events (transfers): {cooperation_events}")
    print(f"   Communication events (signals): {communication_events}")
    print(f"   Observation events: {observation_events}")
    print(f"   Learning events (stored knowledge): {learning_events}")
    
    # Analyze relationships
    relationships = memory.relationships
    if relationships:
        print(f"\n🤝 Relationship Analysis:")
        for rel, strength in relationships.items():
            agent_a, agent_b = rel.split('->')
            rel_type = "trust" if strength > 0 else "distrust" if strength < 0 else "neutral"
            print(f"   {agent_a} -> {agent_b}: {strength:.2f} ({rel_type})")
    
    # Show discovered patterns
    if memory.patterns:
        print(f"\n🧩 Discovered Patterns:")
        for pattern in memory.patterns:
            print(f"   '{pattern['name']}': {pattern['description']} (confidence: {pattern['confidence']:.2f})")
    
    # Show memory search capability
    print(f"\n🔍 Memory Search Demo:")
    results = memory.search_similar("cooperation", top_k=3)
    print(f"   Searching for 'cooperation' found {len(results)} relevant events")
    
    if results:
        for i, result in enumerate(results[:2]):
            print(f"   {i+1}. {result['actor']} {result['action']}: {result['reasoning'][:50]}...")

if __name__ == "__main__":
    demo_emergence()
