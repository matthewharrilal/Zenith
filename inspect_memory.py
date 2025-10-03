#!/usr/bin/env python3
"""
Memory Inspector - View what's stored in memory.pkl
Usage: python3 inspect_memory.py [memory_file]
"""

import sys
import pickle
from pathlib import Path

def inspect_memory(filename="memory.pkl"):
    """Inspect the contents of a memory file"""
    try:
        with open(filename, 'rb') as f:
            data = pickle.load(f)
        
        print(f"📚 MEMORY INSPECTOR: {filename}")
        print("=" * 60)
        
        # Events
        events = data.get('events', [])
        print(f"📊 Total Events: {len(events)}")
        
        if events:
            print(f"\n🔍 Recent Events (last 5):")
            for event in events[-5:]:
                print(f"   {event['actor']} → {event['action']} (ID: {event['id']})")
                if 'reasoning' in event and event['reasoning']:
                    reasoning_preview = event['reasoning'][:100] + "..." if len(event['reasoning']) > 100 else event['reasoning']
                    print(f"      💭 {reasoning_preview}")
                print()
        
        # Patterns
        patterns = data.get('patterns', [])
        print(f"🧩 Total Patterns: {len(patterns)}")
        
        if patterns:
            print(f"\n💡 Discovered Patterns:")
            for pattern in patterns:
                print(f"   • {pattern['name']}: {pattern['description']}")
                print(f"     Confidence: {pattern['confidence']:.2f} | By: {pattern['discovered_by']}")
                print()
        
        # Relationships
        relationships = data.get('relationships', {})
        print(f"👥 Relationships: {len(relationships)}")
        
        if relationships:
            print(f"\n🤝 Agent Relationships:")
            for rel, strength in relationships.items():
                status = "🤝 Trust" if strength > 0.3 else "😐 Neutral" if strength > -0.3 else "😡 Distrust"
                print(f"   {rel}: {strength:.2f} {status}")
        
        # Metadata
        metadata = data.get('metadata', {})
        if metadata:
            print(f"\n📈 Metadata:")
            for key, value in metadata.items():
                print(f"   {key}: {value}")
                
    except FileNotFoundError:
        print(f"❌ Memory file '{filename}' not found")
    except Exception as e:
        print(f"❌ Error reading memory file: {e}")

if __name__ == "__main__":
    filename = sys.argv[1] if len(sys.argv) > 1 else "memory.pkl"
    inspect_memory(filename)
