# Development Guide

## Setup

### Quick Start
```bash
./quickstart.sh
```

This script will:
- Create virtual environment
- Install all dependencies
- Set up .env configuration
- Start Docker services (if available)
- Run tests to verify setup

### Manual Setup

1. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   make install-dev
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

4. **Start infrastructure** (optional):
   ```bash
   make docker-up
   ```

## Running Examples

### 1. Simple Agent (No External Services)
```bash
export OPENAI_API_KEY="your-key"
python examples/simple_agent.py
```

### 2. Tool-Using Agent
```bash
python examples/tool_using_agent.py
```

### 3. RAG Agent (Requires ChromaDB)
```bash
pip install chromadb
python examples/rag_agent.py
```

### 4. Multi-Agent System (Requires Redis - Optional)
```bash
docker-compose up -d redis
python examples/multi_agent_system.py
```

## Running the API Server

### Development Mode
```bash
python src/api/rest.py
```

Visit:
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Metrics: http://localhost:9090/metrics

### Production Mode
```bash
uvicorn src.api.rest:app --host 0.0.0.0 --port 8000 --workers 4
```

## Testing

### Run All Tests
```bash
make test
```

### Run Unit Tests Only
```bash
pytest -m unit
```

### Run with Coverage
```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Run Specific Test
```bash
pytest tests/test_domain_models.py::TestAgent::test_create_agent -v
```

## Development Workflow

### Code Quality Checks

```bash
# Format code
make format

# Lint code
make lint

# Type check
make type-check

# Run all checks
make format lint type-check test
```

### Pre-commit Hooks

Install pre-commit hooks to run checks automatically:

```bash
pre-commit install
```

Note: Currently requires Python 3.11. To commit without hooks:
```bash
git commit --no-verify -m "message"
```

## Project Structure

```
src/
├── domain/           # Business logic
│   ├── models.py     # Entities (Agent, Message, Tool)
│   ├── interfaces.py # Service contracts
│   └── exceptions.py # Domain errors
│
├── application/      # Use cases
│   ├── orchestrator.py  # Agent execution engine
│   └── use_cases.py     # Business workflows
│
├── infrastructure/   # External services
│   ├── llm_providers.py   # OpenAI, Anthropic
│   ├── vector_stores.py   # Qdrant, Chroma
│   ├── message_queue.py   # Redis
│   ├── repositories.py    # Data access
│   └── observability.py   # Logging, metrics
│
├── api/              # HTTP endpoints
│   └── rest.py       # FastAPI application
│
├── tools/            # Built-in tools
│   ├── calculator.py
│   ├── web_search.py
│   ├── file_operations.py
│   ├── code_execution.py
│   └── registry.py
│
└── config.py         # Configuration management
```

## Adding New Features

### 1. Adding a New Tool

```python
# src/tools/my_tool.py
def my_tool_handler(param1: str, param2: int) -> dict:
    """Tool implementation."""
    return {"result": "..."}

# Register in registry
from src.domain.models import Tool, ToolParameter

tool = Tool(
    name="my_tool",
    description="What the tool does",
    parameters=[
        ToolParameter(name="param1", type="string", description="...", required=True),
        ToolParameter(name="param2", type="integer", description="...", required=False),
    ],
    handler_module="src.tools.my_tool",
    handler_function="my_tool_handler",
)
tool_registry.register_tool(tool)
```

### 2. Adding a New LLM Provider

```python
# src/infrastructure/llm_providers.py
from src.domain.interfaces import ILLMProvider

class MyLLMProvider(ILLMProvider):
    async def generate_completion(self, messages, model, **kwargs):
        # Implementation
        pass
    
    async def get_embedding(self, text, model):
        # Implementation
        pass
```

### 3. Adding a New API Endpoint

```python
# src/api/rest.py
@app.post("/my-endpoint")
async def my_endpoint(request: MyRequest):
    # Implementation
    pass
```

## Debugging

### Enable Debug Logging
```bash
export LOG_LEVEL=DEBUG
python examples/simple_agent.py
```

### Interactive Debugging
```python
import pdb; pdb.set_trace()
```

### View Logs
```bash
# Structured JSON logs
tail -f logs/app.log | jq

# Docker service logs
docker-compose logs -f redis
```

## Monitoring

### Prometheus Metrics
- Exposed on port 9090
- Visit http://localhost:9090/metrics

### Jaeger Tracing
- UI on port 16686
- Visit http://localhost:16686

### Health Checks
```bash
curl http://localhost:8000/health
```

## Common Issues

### Issue: OPENAI_API_KEY not set
**Solution**: Export the key or add to .env
```bash
export OPENAI_API_KEY="sk-..."
```

### Issue: Redis connection error
**Solution**: Start Redis or disable message queue
```bash
docker-compose up -d redis
```

### Issue: Port already in use
**Solution**: Stop conflicting service or change port
```bash
lsof -ti:8000 | xargs kill -9
```

### Issue: ModuleNotFoundError
**Solution**: Ensure virtual environment is activated
```bash
source venv/bin/activate
pip install -e ".[dev]"
```

## Performance Tips

1. **Use GPT-3.5-turbo for development** (cheaper, faster)
2. **Cache embeddings** for repeated texts
3. **Set lower max_tokens** during testing
4. **Use temperature=0** for deterministic responses
5. **Monitor token usage** in metrics

## Security Checklist

- [ ] API keys in environment variables (never commit)
- [ ] File operations restricted to allowed directories
- [ ] Code execution sandboxed (use Docker in production)
- [ ] Rate limiting enabled on expensive operations
- [ ] Input validation on all endpoints
- [ ] CORS configured for your domain
- [ ] HTTPS in production
- [ ] Secrets in dedicated vault (not .env)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run quality checks
5. Submit pull request

## Getting Help

- 📖 Read the [README](../README.md)
- 📝 Check [examples](../examples/)
- 🐛 Report issues on GitHub
- 💬 Ask questions in discussions
