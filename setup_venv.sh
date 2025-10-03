#!/bin/bash
# Emergent Intelligence System - Virtual Environment Setup Script

echo "🧠 EMERGENT INTELLIGENCE SYSTEM - VIRTUAL ENVIRONMENT SETUP"
echo "============================================================"

# Check Python version
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

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
echo "✅ VIRTUAL ENVIRONMENT SETUP COMPLETE!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Create your .env file:"
echo "   cp env.example .env"
echo "   # Then edit .env and add your OpenAI API key"
echo ""
echo "3. Run your first game:"
echo "   python3 src/main.py --games 1"
echo ""
echo "4. Run multiple games to see emergence:"
echo "   python3 src/main.py --games 10 --memory-file memory.pkl"
echo ""
echo "To deactivate the virtual environment later:"
echo "   deactivate"
