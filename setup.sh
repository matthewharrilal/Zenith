#!/bin/bash
# Emergent Intelligence System Setup Script

echo "🧠 EMERGENT INTELLIGENCE SYSTEM SETUP"
echo "======================================"

# Check Python version
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Test system
echo "🧪 Testing system components..."
python3 test_system.py

if [ $? -ne 0 ]; then
    echo "❌ System test failed"
    exit 1
fi

echo ""
echo "✅ SETUP COMPLETE!"
echo ""
echo "Next steps:"
echo "1. Set your OpenAI API key:"
echo "   export OPENAI_API_KEY='your-key-here'"
echo ""
echo "2. Run your first game:"
echo "   python3 src/main.py --games 1"
echo ""
echo "3. Run multiple games to see emergence:"
echo "   python3 src/main.py --games 10 --memory-file memory.pkl"
echo ""
echo "4. Read the README.md for more details"
