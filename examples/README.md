# Examples

This directory contains practical examples demonstrating the AI Agents platform capabilities.

## Getting Started

Before running examples, ensure you have:

1. **Installed dependencies**:
   ```bash
   make install-dev
   ```

2. **Set your OpenAI API key**:
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

3. **Started infrastructure** (for some examples):
   ```bash
   make docker-up
   ```

## Examples Overview

### 1. Simple Agent (`simple_agent.py`)
**Difficulty**: Beginner  
**Dependencies**: OpenAI API key only

Basic agent that answers questions without tools. Perfect for getting started.

```bash
python examples/simple_agent.py
```

**What you'll learn**:
- Creating and configuring agents
- Basic agent execution
- Viewing metrics (tokens, cost, duration)

---

### 2. Tool-Using Agent (`tool_using_agent.py`)
**Difficulty**: Intermediate  
**Dependencies**: OpenAI API key only

Agent with multiple tools for calculations, time queries, and documentation search.

```bash
python examples/tool_using_agent.py
```

**What you'll learn**:
- Creating custom tools
- Tool registration and permissions
- How agents decide when to use tools
- Chaining multiple tool calls

---

### 3. RAG Agent (`rag_agent.py`)
**Difficulty**: Intermediate  
**Dependencies**: OpenAI API key, ChromaDB

Agent using Retrieval-Augmented Generation with semantic search.

```bash
python examples/rag_agent.py
```

**What you'll learn**:
- Setting up vector databases
- Semantic search for knowledge retrieval
- Grounding LLM responses in factual data
- Building question-answering systems

**Note**: Creates `./chroma_data/` directory for persistence.

---

### 4. Multi-Agent System (`multi_agent_system.py`)
**Difficulty**: Advanced  
**Dependencies**: OpenAI API key, Redis (optional)

Multiple specialized agents collaborating on complex tasks.

```bash
# Start Redis (optional)
docker-compose up -d redis

python examples/multi_agent_system.py
```

**What you'll learn**:
- Coordinating multiple agents
- Specialized agent roles (planner, researcher, executor, reviewer)
- Workflow orchestration
- Inter-agent communication

---

### 5. Streaming Agent (`streaming_agent.py`)
**Difficulty**: Intermediate  
**Dependencies**: OpenAI API key only

Real-time token streaming for better UX in chat interfaces.

```bash
python examples/streaming_agent.py
```

**What you'll learn**:
- Streaming vs non-streaming responses
- Real-time token delivery
- Server-sent events (SSE) pattern
- When to use streaming mode

**Features**:
- Side-by-side comparison of streaming vs non-streaming
- Live token display
- Performance metrics
- API integration examples

---

### 6. Streaming Client (`streaming_client.py`)
**Difficulty**: Beginner  
**Dependencies**: API server running

Interactive client for testing the streaming API endpoint.

```bash
# Terminal 1: Start API server
python src/api/rest.py

# Terminal 2: Run client
python examples/streaming_client.py

# Or with existing agent
python examples/streaming_client.py --agent-id <uuid>

# Demo mode
python examples/streaming_client.py --mode demo
```

**What you'll learn**:
- Consuming streaming APIs
- Server-sent events (SSE) client
- Interactive chat interfaces
- Real-time response handling

---

### 7. Database Persistence (`database_persistence.py`)
**Difficulty**: Intermediate  
**Dependencies**: OpenAI API key, PostgreSQL

Production-ready persistence with conversation history.

```bash
# Start PostgreSQL
docker-compose up -d postgres

# Run example
python examples/database_persistence.py
```

**What you'll learn**:
- PostgreSQL repository usage
- Conversation history persistence
- Database migrations
- Connection pooling
- Production deployment patterns

**Features**:
- ACID transaction support
- Efficient indexing
- Conversation history across restarts
- Multi-agent shared state

---

### 8. Agent Templates (`agent_templates.py`)
**Difficulty**: Beginner
**Dependencies**: OpenAI API key only

Pre-built specialized agents for common use cases.

```bash
python examples/agent_templates.py
```

**What you'll learn**:
- Using pre-configured agent templates
- Quick agent creation without prompt engineering
- Specialized agent configurations
- Template customization

**Available templates**:
- Code Reviewer - Reviews code quality
- SQL Generator - Converts English to SQL
- Documentation Writer - Generates docs
- Data Analyst - Analyzes data
- Research Assistant - Researches topics
- Customer Support - Empathetic support
- Content Creator - Marketing content
- System Architect - Designs architectures

---

### 9. Rate Limiting (`rate_limiting.py`)
**Difficulty**: Intermediate
**Dependencies**: OpenAI API key only

Cost control and usage quotas to prevent runaway expenses.

```bash
python examples/rate_limiting.py
```

**What you'll learn**:
- Request and token limits
- Cost caps per time window
- Per-user quotas
- Emergency stop functionality
- Usage monitoring

**Features**:
- Multi-window rate limiting (minute/hour/day)
- Token and cost budgets
- Burst allowance
- Real-time usage tracking
- Emergency kill switch

---

### 10. Memory Agent (`memory_agent.py`)
**Difficulty**: Intermediate
**Dependencies**: OpenAI API key, PostgreSQL

Agents with conversation memory and context retention across sessions.

```bash
# Start PostgreSQL
docker-compose up -d postgres

python examples/memory_agent.py
```

**What you'll learn**:
- Conversation memory with session management
- Context retention across multiple turns
- Importance scoring for memory prioritization
- Semantic search over conversation history
- Session-based memory isolation

**Features**:
- Automatic context storage
- Smart memory retrieval based on relevance
- Importance weighting (critical info vs casual chat)
- Session history management
- Memory search with similarity scoring

---

### 11. Gmail Cleanup Agent (`gmail_cleanup_agent.py`)
**Difficulty**: Intermediate
**Dependencies**: OpenAI API key, Gmail API OAuth credentials

AI assistant that manages your Gmail inbox using natural language commands.

```bash
# Install Gmail dependencies
pip install -e ".[gmail]"

# Set up OAuth credentials (one-time)
# See docs/GMAIL_SETUP.md for detailed instructions

# Run interactive cleanup assistant
python examples/gmail_cleanup_agent.py
```

**What you'll learn**:
- OAuth2 authentication with Google APIs
- Gmail API integration for email management
- Safe bulk operations with confirmation prompts
- Natural language email management
- Production-ready tool safety patterns

**Example commands**:
- "Show me my unread emails"
- "Delete all emails from notifications@linkedin.com"
- "Archive promotional emails older than 90 days"
- "Clean up emails from the last year"

**Safety features**:
- Confirmation required for bulk deletions
- Batch limits (100-200 emails max per operation)
- List-first approach (always shows what will be affected)
- Archive option (safer than permanent deletion)
- Trash support (30-day recovery window)

📖 **[Complete Gmail Setup Guide](../docs/GMAIL_SETUP.md)**

---

## Business Agent Examples (Production-Ready)

The following agents are production-ready implementations matching the services offered on our landing page. Each includes comprehensive tools, integration documentation, and test scenarios.

### 12. Email & Social Media Automation Agent (`email_social_automation_agent.py`)
**Difficulty**: Intermediate  
**Dependencies**: OpenAI API key  
**Use Case**: Automate customer communication across email and social platforms

```bash
python examples/email_social_automation_agent.py
```

**What you'll learn**:
- Multi-platform communication automation
- Sentiment analysis and message classification
- Tone matching and platform-specific formatting
- Response generation with context awareness

**Tools included (5)**:
- `analyze_sentiment` - Detect emotion and urgency in messages
- `classify_message` - Categorize as inquiry, complaint, appreciation, etc.
- `generate_email_response` - Create professional email replies
- `generate_social_response` - Platform-specific social media responses
- `schedule_message` - Queue messages for optimal timing

**Platforms supported**:
- Gmail (Email)
- Twitter (280 char limit)
- LinkedIn (3000 chars)
- Facebook (8000 chars)
- Instagram (2200 chars)

**Integration APIs**:
- Gmail API, Twitter API, LinkedIn API, Facebook Graph API, Instagram API

---

### 13. Data Processing Agent (`data_processing_agent.py`)
**Difficulty**: Intermediate  
**Dependencies**: OpenAI API key  
**Use Case**: Automate data entry, validation, cleaning, and transformation

```bash
python examples/data_processing_agent.py
```

**What you'll learn**:
- Extract structured data from unstructured text
- Validate data against business rules
- Transform between formats (CSV, JSON, XML, Excel)
- Detect duplicates and clean inconsistent data
- Generate data quality reports

**Tools included (6)**:
- `extract_data_from_text` - Pull contact info, invoices, addresses from text
- `validate_data` - Check data against validation rules
- `transform_data_format` - Convert between CSV, JSON, XML, Excel
- `detect_duplicates` - Find duplicate records with fuzzy matching
- `clean_data` - Fix formatting, trim whitespace, standardize values
- `generate_quality_report` - Score completeness, accuracy, consistency

**Data types supported**:
- Contact information (name, email, phone, address)
- Invoices (invoice number, date, amount, vendor, customer)
- Addresses (street, city, state, zip, country)

**Integration APIs**:
- Google Sheets API, Airtable API, Salesforce API, QuickBooks API, OCR engines

---

### 14. Appointment Booking Agent (`appointment_booking_agent.py`)
**Difficulty**: Intermediate  
**Dependencies**: OpenAI API key  
**Use Case**: Automate appointment scheduling, calendar management, and reminders

```bash
python examples/appointment_booking_agent.py
```

**What you'll learn**:
- Calendar availability checking across multiple resources
- Smart slot finding with business rules
- Automated booking confirmations
- Rescheduling and cancellation workflows
- Multi-reminder system (24h, 2h, 15min before)

**Tools included (7)**:
- `check_availability` - Verify if specific time slot is available
- `find_available_slots` - Search for open slots within date range
- `create_booking` - Book appointment with details
- `send_booking_confirmation` - Email/SMS confirmation to customer
- `reschedule_appointment` - Move existing appointment to new time
- `cancel_appointment` - Cancel with notification
- `send_appointment_reminder` - Automated reminder emails/SMS

**Features**:
- Business hours enforcement (Mon-Fri 9 AM - 5 PM, excludes lunch)
- Time zone conversion (PST/PDT support)
- Buffer time management (15 min between appointments)
- Multi-calendar support

**Integration APIs**:
- Google Calendar API, Microsoft Outlook API, Calendly API, Zoom API, Twilio (SMS), SendGrid (email)

---

### 15. Customer Service Chatbot Agent (`customer_service_chatbot_agent.py`)
**Difficulty**: Intermediate  
**Dependencies**: OpenAI API key  
**Use Case**: 24/7 automated customer support with smart escalation

```bash
python examples/customer_service_chatbot_agent.py
```

**What you'll learn**:
- Knowledge base search for instant answers
- Order status tracking and account information
- Support ticket creation for complex issues
- Smart escalation to human agents
- Refund processing with approval workflows
- Customer satisfaction tracking

**Tools included (7)**:
- `search_knowledge_base` - Search KB for pricing, features, support info
- `check_order_status` - Look up current order progress
- `get_account_information` - Retrieve customer account details
- `create_support_ticket` - Create ticket for technical issues
- `escalate_to_human` - Escalate complex/sensitive issues to humans
- `process_refund_request` - Handle refund requests
- `track_customer_satisfaction` - Record CSAT scores and feedback

**Escalation triggers**:
- Customer is angry/frustrated
- Technical issues beyond chatbot capability
- Refund requests over $1000
- Customer specifically requests human

**Integration APIs**:
- Zendesk API, Intercom API, Freshdesk API, Stripe (refunds), custom knowledge base

**Business impact**:
- Reduce support costs by 60-80%
- Instant response time (vs hours)
- Handle 10x more inquiries
- 24/7 availability

---

## Example Output

Each example provides detailed output including:
- **Agent responses**: The actual answers/results
- **Execution metrics**: Tokens used, duration, iterations
- **Cost tracking**: Estimated API costs
- **Process visibility**: What the agent is doing at each step

## Customization

All examples are self-contained and can be easily modified:

1. **Change models**: Edit `model_name` (e.g., `gpt-3.5-turbo` for lower cost)
2. **Adjust behavior**: Modify `system_prompt` for different personalities
3. **Add tools**: Create new tool handlers and register them
4. **Tune parameters**: Adjust `temperature`, `max_tokens`, `max_iterations`

## Tips

- **Start small**: Begin with `simple_agent.py` before advanced examples
- **Monitor costs**: Check metrics output to understand API usage
- **Experiment**: Modify prompts and parameters to see effects
- **Read code**: Examples are heavily commented for learning

## Troubleshooting

**"OPENAI_API_KEY not set"**
```bash
export OPENAI_API_KEY="your-key-here"
```

**Redis connection error (multi-agent example)**
```bash
docker-compose up -d redis
# Or run without Redis - it's optional
```

**ChromaDB issues (RAG example)**
```bash
pip install chromadb
# Or use Qdrant with docker-compose
```

## Next Steps

After running examples:

1. **Build your own agent**: Combine concepts from multiple examples
2. **Create custom tools**: Implement domain-specific capabilities
3. **Add persistence**: Use PostgreSQL for production storage
4. **Build an API**: Wrap agents in FastAPI endpoints
5. **Deploy to production**: Follow the deployment guide

## Contributing

Found an issue or have an idea for a new example? Please open an issue or PR!
