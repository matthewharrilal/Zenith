# Emergent Intelligence System

A system that demonstrates how complex social behaviors can emerge from simple primitive tools and memory accumulation. Agents develop strategies, cooperation patterns, and social dynamics through experimentation with 10 basic tools.

## Quick Start

### 1. Setup Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set OpenAI API key
export OPENAI_API_KEY="your-key-here"
```

### 2. Run First Test
```bash
# Run a single game
python src/main.py --games 1

# Run multiple games to see emergence
python src/main.py --games 10 --memory-file memory.pkl
```

## How It Works

### Core Philosophy
- **10 Primitive Tools**: Agents can only use these basic functions to interact with the world
- **Memory Accumulation**: Learning happens across games through persistent memory
- **No Predefined Behaviors**: Agents discover everything through experimentation
- **Social Pressure**: Multi-agent dynamics force cooperation/betrayal decisions

### The 10 Primitive Tools
1. `observe(entity, resolution)` - Gather information
2. `query(memory_type, search)` - Search collective memory
3. `detect(entities, pattern)` - Find patterns in data
4. `transfer(property, from, to, amount)` - Move resources/properties
5. `modify(entity, property, operation, value)` - Change entity properties
6. `connect(entity_a, entity_b, strength)` - Create/modify relationships
7. `signal(message, intensity, target)` - Send communication
8. `receive(filters, window)` - Listen for signals
9. `store(knowledge, confidence)` - Save discoveries
10. `compute(inputs, operation)` - Process information

### Expected Emergence Timeline
- **Games 1-3**: Tool discovery, basic resource sharing
- **Games 4-10**: Trust verification methods, simple strategies
- **Games 11-25**: Complex social manipulation, alliance warfare
- **Games 26+**: Meta-awareness, philosophical reasoning about cooperation

## Scenarios

### Safe House Scenario
Three agents (RAVEN, FALCON, VIPER) wake up in a compromised safe house. They must work together to escape before discovery, but trust is uncertain and resources are limited.

## Cost Management
- Uses GPT-4o-mini for cost efficiency (~$0.015 per game)
- Tracks API usage and provides cost estimates
- Memory persistence reduces redundant learning

## File Structure
```
src/
├── main.py                 # CLI entry point
├── core/
│   ├── memory.py          # Memory system with vector search
│   ├── game_state.py      # Flexible entity management
│   ├── primitives.py      # 10 primitive tools
│   ├── agents.py          # Agent classes with GPT integration
│   └── engine.py          # Game orchestration
└── requirements.txt       # Dependencies
```

## Advanced Usage

### Run Long Emergence Study
```bash
# Run 50 games with persistent memory
python src/main.py --games 50 --memory-file long_study.pkl --max-time 1000
```

### Analyze Memory Patterns
```python
# Load and analyze discovered patterns
import pickle
with open('memory.pkl', 'rb') as f:
    data = pickle.load(f)
    patterns = data['patterns']
    print(f"Discovered {len(patterns)} patterns")
```

## Success Metrics
- **Cooperation Events**: Resource sharing and collaboration
- **Communication Events**: Signal exchanges and protocols
- **Pattern Discovery**: Strategies and insights stored in memory
- **Social Dynamics**: Trust networks and relationship evolution
- **Tool Creativity**: Novel uses of primitive functions

## Troubleshooting

### Common Issues
1. **OpenAI API Key**: Make sure `OPENAI_API_KEY` environment variable is set
2. **Memory Errors**: Delete `memory.pkl` to start fresh
3. **Cost Concerns**: Use `--max-time` to limit game duration

### Debug Mode
Add print statements in `core/engine.py` to see detailed agent reasoning and action execution.

## Contributing
This is a research system focused on emergence. Key areas for enhancement:
- Additional primitive tools (carefully chosen)
- New scenarios with different social pressures
- Enhanced pattern detection algorithms
- Visualization of emergent behaviors

## License
MIT License - Feel free to experiment and extend!
