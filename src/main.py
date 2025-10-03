#!/usr/bin/env python3
"""
Emergent Intelligence System - Main CLI
Run: python main.py --games 10 --scenario safehouse
"""

import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from core.engine import GameEngine

def main():
    parser = argparse.ArgumentParser(description='Emergent Intelligence System')
    parser.add_argument('--scenario', default='safehouse', help='Scenario to run')
    parser.add_argument('--games', type=int, default=1, help='Number of games')
    parser.add_argument('--memory-file', type=str, default='memory.pkl', help='Memory persistence file')
    parser.add_argument('--max-time', type=float, default=500.0, help='Max time per game')
    parser.add_argument('--openai-key', type=str, help='OpenAI API key (or use OPENAI_API_KEY env var)')
    
    args = parser.parse_args()
    
    # Setup OpenAI API key
    if args.openai_key:
        os.environ['OPENAI_API_KEY'] = args.openai_key
    elif not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OpenAI API key required. Set OPENAI_API_KEY env var or use --openai-key")
        sys.exit(1)
    
    print("\n🧠 EMERGENT INTELLIGENCE SYSTEM")
    print("=" * 60)
    print(f"Scenario: {args.scenario}")
    print(f"Games: {args.games}")
    print(f"Memory file: {args.memory_file}")
    print("=" * 60)
    print()
    
    # Initialize game engine
    engine = GameEngine()
    
    # Load persistent memory if exists
    if os.path.exists(args.memory_file):
        engine.load_memory(args.memory_file)
        print(f"📚 Loaded {len(engine.memory.events)} events from memory")
        print(f"🧩 Loaded {len(engine.memory.patterns)} discovered patterns")
        print("-" * 60)
    
    # Run multiple games
    all_results = []
    total_cost_estimate = 0.0
    
    for game_num in range(args.games):
        # Smart game header with progress
        progress = f"[{game_num + 1}/{args.games}]"
        print(f"\n🎮 GAME {progress} │ Safe House Escape")
        print("─" * 50)
        
        try:
            # Setup scenario
            engine.setup_scenario(args.scenario)
            
            # Run simulation
            result = engine.run_simulation(args.max_time)
            all_results.append(result)
            
            # Estimate cost (enhanced reasoning calculation)
            total_actions = result.get('total_actions', 0)
            estimated_tokens = total_actions * 1200  # ~1200 tokens per action (enhanced reasoning)
            game_cost = estimated_tokens * 0.00015 / 1000  # GPT-4o-mini rate
            total_cost_estimate += game_cost
            
            # Compact game completion
            print(f"\n✅ GAME {progress} COMPLETE │ Actions: {total_actions} │ Cost: ${game_cost:.4f}")
            print(f"📚 Memory: {len(engine.memory.events)} events, {len(engine.memory.patterns)} patterns")
            
            # Save memory after each game
            engine.save_memory(args.memory_file)
            print(f"💾 Memory saved to {args.memory_file}")
            
        except KeyboardInterrupt:
            print("\n⏸️ Simulation interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Error in game {game_num + 1}: {e}")
            continue
    
    # Final analysis
    print(f"\n{'🏆'*20}")
    print("🏆 SESSION SUMMARY")
    print(f"{'🏆'*20}")
    print(f"🎮 Games completed: {len(all_results)}")
    print(f"💵 Total estimated cost: ${total_cost_estimate:.4f}")
    print(f"📚 Total events in memory: {len(engine.memory.events)}")
    print(f"🧩 Total patterns discovered: {len(engine.memory.patterns)}")
    if len(all_results) > 0:
        print(f"⏱️  Average time per game: {sum(r.get('duration', 0) for r in all_results) / len(all_results):.1f}s")
    else:
        print(f"⏱️  Average time per game: N/A (no games completed)")
    
    # Emergence analysis
    if len(all_results) > 1:
        print(f"\n{'🔬'*20}")
        print("🔬 EMERGENCE ANALYSIS")
        print(f"{'🔬'*20}")
        cooperation_trend = [r.get('cooperation_events', 0) for r in all_results]
        communication_trend = [r.get('communication_events', 0) for r in all_results]
        
        print(f"🤝 Cooperation events per game: {cooperation_trend}")
        print(f"📡 Communication events per game: {communication_trend}")
        
        if len(cooperation_trend) > 3:
            recent_coop = sum(cooperation_trend[-3:]) / 3
            early_coop = sum(cooperation_trend[:3]) / 3 if len(cooperation_trend) >= 3 else 0
            
            print(f"\n📊 COOPERATION TREND ANALYSIS:")
            print(f"   Early games average: {early_coop:.1f} cooperation events")
            print(f"   Recent games average: {recent_coop:.1f} cooperation events")
            
            if recent_coop > early_coop * 1.5:
                print("   📈 EMERGENCE DETECTED: Cooperation strategies developing!")
            elif recent_coop < early_coop * 0.5:
                print("   📉 PATTERN: Agents becoming more competitive over time")
            else:
                print("   📊 PATTERN: Stable cooperation levels maintained")
    
    print(f"\n🎯 Next steps: Run more games to see deeper emergence patterns")
    print(f"💡 Try: python main.py --games 50 --memory-file {args.memory_file}")

if __name__ == "__main__":
    main()
