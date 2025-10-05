#!/usr/bin/env python3
"""
Example: Using the Balanced Visual Display System

This demonstrates the new balanced visual output design that provides
informative but not overwhelming display of simulation dynamics.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.engine import GameEngine

def run_balanced_simulation():
    """Run a simulation with the new balanced visual display"""
    
    print("🎯 BALANCED VISUAL DISPLAY EXAMPLE")
    print("=" * 50)
    print("This demonstrates the new three-column layout:")
    print("• Actions: What each agent is doing")
    print("• Memory/Patterns: Memory queries and storage")
    print("• State: Health bars and resource indicators")
    print("• Key Events: Only significant interactions")
    print("• Pattern Insights: Periodic behavior analysis")
    print("=" * 50)
    
    # Create and setup simulation
    engine = GameEngine()
    engine.setup_scenario("safehouse")
    
    print("\n🚀 Running simulation with balanced display...")
    print("Press Ctrl+C to stop early\n")
    
    try:
        # Run a few rounds to demonstrate the display
        for round_num in range(1, 8):
            print(f"\n{'='*60}")
            print(f"ROUND {round_num} - Balanced Display Demo")
            print(f"{'='*60}")
            
            # Run the round with balanced display
            engine.run_round()
            
            # Add a small delay for readability
            import time
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Simulation stopped by user")
    
    print("\n✅ Example completed!")
    print("\nKey features demonstrated:")
    print("• Clean three-column layout")
    print("• Smart action formatting with icons")
    print("• Memory pattern tracking")
    print("• Key events highlighting")
    print("• Pattern insights detection")
    print("• Health and resource indicators")

if __name__ == "__main__":
    run_balanced_simulation()
