#!/bin/bash
# Quick Start Script for AI Agents Platform

set -e

echo "🚀 AI Agents Platform - Quick Start"
echo "===================================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Found Python $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -e ".[dev,openai,anthropic,vectordb,observability]"
echo "✓ Dependencies installed"

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "⚙️  Setting up environment configuration..."
    cp .env.example .env
    echo "✓ Created .env file from template"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your API keys:"
    echo "   - OPENAI_API_KEY=your_key_here"
    echo "   - ANTHROPIC_API_KEY=your_key_here (optional)"
    echo ""
    read -p "Press Enter after you've added your API keys to .env..."
fi

# Create workspace directories for file operations
echo ""
echo "📁 Creating workspace directories..."
mkdir -p workspace data output
echo "✓ Workspace directories created"

# Check for Docker
if command -v docker &> /dev/null; then
    echo ""
    echo "🐳 Docker found. Starting infrastructure services..."
    if docker-compose up -d 2>/dev/null; then
        echo "✓ Infrastructure services started:"
        echo "   - Redis (localhost:6379)"
        echo "   - Qdrant (localhost:6333)"
        echo "   - Jaeger (localhost:16686)"
        echo "   - Prometheus (localhost:9091)"
    else
        echo "⚠️  Could not start Docker services (optional)"
    fi
else
    echo ""
    echo "⚠️  Docker not found. Infrastructure services not started (optional)"
    echo "   You can still run examples that don't require Redis/Qdrant"
fi

# Run tests
echo ""
echo "🧪 Running tests to verify setup..."
if pytest -q -m unit 2>/dev/null; then
    echo "✓ All tests passed"
else
    echo "⚠️  Some tests failed, but you can still proceed"
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📚 Next Steps:"
echo ""
echo "1. Try the simple example:"
echo "   python examples/simple_agent.py"
echo ""
echo "2. Explore tool-using agents:"
echo "   python examples/tool_using_agent.py"
echo ""
echo "3. Try RAG (Retrieval-Augmented Generation):"
echo "   python examples/rag_agent.py"
echo ""
echo "4. Start the API server:"
echo "   python src/api/rest.py"
echo "   # Then visit http://localhost:8000/docs"
echo ""
echo "5. Read the documentation:"
echo "   cat README.md"
echo "   cat examples/README.md"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Tip: Run 'source venv/bin/activate' to activate the environment"
echo ""
