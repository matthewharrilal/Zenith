# 🧠 Emergent Intelligence System - Setup Instructions

## Quick Setup

### 1. Create Virtual Environment
```bash
# Run the setup script
./setup_venv.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Create .env File
Create a `.env` file in the project root with your OpenAI API key:

```bash
# Create .env file
cat > .env << EOF
# Emergent Intelligence System Environment Variables
OPENAI_API_KEY=your_actual_openai_api_key_here

# Optional overrides (uncomment to use):
# OPENAI_MODEL=gpt-4o-mini
# OPENAI_TEMPERATURE=0.7
# OPENAI_MAX_TOKENS=400
EOF
```

**Replace `your_actual_openai_api_key_here` with your real OpenAI API key!**

### 3. Test the System
```bash
# Test without API key (free)
python3 test_system.py

# Test with API key
python3 src/main.py --games 1
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ Yes | - | Your OpenAI API key |
| `OPENAI_MODEL` | ❌ No | `gpt-4o-mini` | GPT model to use |
| `OPENAI_TEMPERATURE` | ❌ No | `0.7` | Response creativity (0.0-1.0) |
| `OPENAI_MAX_TOKENS` | ❌ No | `400` | Maximum tokens per response |

## Running the System

### Basic Usage
```bash
# Single game
python3 src/main.py --games 1

# Multiple games to see emergence
python3 src/main.py --games 10 --memory-file memory.pkl

# Long-term study
python3 src/main.py --games 50 --memory-file long_study.pkl
```

### Command Line Options
- `--games N` - Number of games to run (default: 1)
- `--scenario NAME` - Scenario to run (default: safehouse)
- `--memory-file FILE` - Memory persistence file (default: memory.pkl)
- `--max-time SECONDS` - Max time per game (default: 500)
- `--openai-key KEY` - Override API key from command line

## Troubleshooting

### Common Issues

1. **"OPENAI_API_KEY environment variable not set"**
   - Make sure you created the `.env` file
   - Check that your API key is correct
   - Ensure the virtual environment is activated

2. **"Module not found" errors**
   - Make sure virtual environment is activated: `source venv/bin/activate`
   - Reinstall dependencies: `pip install -r requirements.txt`

3. **API errors**
   - Check your OpenAI API key is valid
   - Ensure you have credits in your OpenAI account
   - Try a different model by setting `OPENAI_MODEL` in `.env`

### Getting Help
- Check the README.md for detailed usage
- Run `python3 demo.py` to see a free demo
- Run `python3 test_system.py` to test components
