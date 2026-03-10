# 🚀 AgentFlow Framework v2.0 - Grok AI Powered

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A production-ready, open-source AI agent orchestration framework with **Grok LLM** (via Groq), drag-and-drop workflow builder, persistent database memory, and dynamic tool creation.

## ✨ Features

### 🧠 **Grok AI Integration**
- **Default LLM**: Groq-powered Llama3 (Grok AI) with ultra-fast inference
- **Persistent Memory**: SQLite/PostgreSQL-backed conversation history
- **Multi-LLM Fallback**: Automatic failover to OpenAI, Anthropic, Gemini, etc.
- **Session Management**: Conversation history per session with configurable window size

### 🎨 **Drag-and-Drop Workflow Builder**
- **React Flow UI**: Visual workflow graph editor
- **Node Types**: LLM nodes, tool nodes, input nodes
- **Live Editing**: Add nodes, connect edges, save workflows to database
- **Workflow Execution**: Run workflows with Grok LLM processing each node

### 🛠️ **Dynamic Tool Creation**
- **UI-Based Creation**: Create tools through the web interface
- **Python Code Execution**: Write custom Python code for tools
- **Database Persistence**: All tools saved to DB
- **Runtime Registration**: Auto-register tools in the framework

### 💾 **Full Database Persistence**
- **SQLAlchemy ORM**: Workflows, tools, agents, conversations, messages, approvals
- **SQLite Default**: Zero config for local development
- **PostgreSQL Ready**: Production-grade async DB support
- **Auto-Init**: Database tables created on startup

### 🤖 **Agent Management**
- **Create Agents**: Define agents with custom system prompts
- **Tool Assignment**: Assign tools to specific agents
- **DB-Backed**: All agent configs persisted

## 🏗️ Architecture

```
agentflow-framework/
├── agentflow/
│   ├── core/
│   │   ├── database.py         # SQLAlchemy models (Workflows, Tools, Agents, Messages)
│   │   ├── config.py           # Settings with Grok/Groq defaults
│   │   └── engine.py
│   ├── llm/
│   │   └── gateway.py          # LiteLLM gateway with DBMemoryManager
│   ├── api/
│   │   ├── main.py             # FastAPI app with DB init
│   │   └── routes/
│   │       ├── workflows.py    # Workflow CRUD + execution
│   │       ├── tools.py        # Tool CRUD + dynamic execution
│   │       └── chat.py         # Grok chat + Agent management
│   └── tools/
│       └── registry.py
├── frontend/
│   └── index.html              # React + React Flow drag-and-drop UI
├── requirements.txt
├── .env.example
└── README.md
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
git clone https://github.com/loolaneshailesh/agentflow-framework.git
cd agentflow-framework
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your Groq API key:
# GROQ_API_KEY=gsk_your_groq_api_key_here
# Get free API key at: https://console.groq.com/keys
```

### 3. Run the Server

```bash
# Using uvicorn directly
uvicorn agentflow.api.main:app --reload

# OR using Python
python -m uvicorn agentflow.api.main:app --reload
```

The server starts at **http://localhost:8000**

### 4. Open the UI

Navigate to **http://localhost:8000** in your browser.

You'll see:
- **Workflows Tab**: Drag-and-drop workflow builder
- **Tools Tab**: Create and manage dynamic tools
- **Chat Tab**: Chat with Grok AI with persistent memory

## 📚 Usage Examples

### Creating a Workflow (UI)

1. Click **"New Workflow"**
2. Name it (e.g., "Customer Support Flow")
3. Add nodes:
   - **Add LLM Node**: Processes text with Grok
   - **Add Tool Node**: Executes a tool
   - **Add Input Node**: Workflow input
4. Connect nodes by dragging edges
5. Click **"Save Canvas"**
6. Click **"Run"** to execute with Grok LLM

### Creating a Custom Tool (UI)

1. Go to **Tools** tab
2. Click **"Create Tool"**
3. Fill in:
   - **Name**: `calculate_discount`
   - **Description**: "Calculates discount based on price"
   - **Python Code**:
   ```python
   price = inputs.get('price', 0)
   discount_pct = inputs.get('discount', 10)
   result = price * (1 - discount_pct / 100)
   ```
4. Click **"Create"**

The tool is now available in workflows!

### Chatting with Grok AI (UI)

1. Go to **Chat (Grok)** tab
2. Type a message: "Explain quantum computing"
3. Grok AI responds with context-aware answers
4. **Memory is persistent**: Previous messages are remembered

### API Usage (cURL)

**Chat with Grok:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is AgentFlow?",
    "session_id": "user123"
  }'
```

**Create Workflow:**
```bash
curl -X POST http://localhost:8000/api/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Data Pipeline",
    "description": "Processes data with AI",
    "nodes": [
      {"id": "llm-1", "type": "default", "position": {"x": 100, "y": 100}, "data": {"label": "LLM Node", "type": "llm"}}
    ],
    "edges": []
  }'
```

**Run Workflow:**
```bash
curl -X POST http://localhost:8000/api/workflows/{workflow_id}/run \
  -H "Content-Type: application/json" \
  -d '{"input_data": {"text": "Analyze this"}}'
```

## ⚙️ Configuration

### Environment Variables (.env)

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | - | **Required**: Groq API key for Grok LLM |
| `ACTIVE_LLM_MODEL` | `groq/llama3-70b-8192` | Default LLM model |
| `DATABASE_URL` | `sqlite:///./agentflow.db` | Database connection string |
| `ENABLE_MEMORY` | `true` | Enable conversation memory |
| `MEMORY_BACKEND` | `db` | Memory backend (db or in_memory) |
| `MEMORY_WINDOW_SIZE` | `20` | Number of messages in context |
| `LOG_LEVEL` | `INFO` | Logging level |

### Supported LLM Models

**Groq (Grok):**
- `groq/llama3-70b-8192`
- `groq/llama3-8b-8192`
- `groq/mixtral-8x7b-32768`
- `groq/gemma2-9b-it`

**Others:**
- OpenAI: `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo`
- Anthropic: `claude-3-5-sonnet-20241022`
- Google: `gemini/gemini-pro`

## 🗃️ Database Schema

```sql
-- Workflows: Store workflow definitions
CREATE TABLE workflows (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  nodes JSON,  -- ReactFlow nodes
  edges JSON,  -- ReactFlow edges
  status TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Tools: Dynamic tool definitions
CREATE TABLE tools (
  id TEXT PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  description TEXT,
  tool_type TEXT,  -- custom, builtin, llm
  parameters JSON,
  code TEXT,  -- Python code
  is_active BOOLEAN,
  created_at TIMESTAMP
);

-- Conversations: Chat sessions
CREATE TABLE conversations (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  agent_id TEXT,
  workflow_id TEXT,
  created_at TIMESTAMP
);

-- Messages: Conversation history
CREATE TABLE messages (
  id TEXT PRIMARY KEY,
  conversation_id TEXT,
  role TEXT,  -- user, assistant, system
  content TEXT,
  created_at TIMESTAMP
);
```

## 🛡️ Security Notes

- **Dynamic Code Execution**: The `code` field in tools executes Python. Use with caution in production.
- **API Keys**: Never commit `.env` to version control
- **CORS**: Default is `*` for dev. Restrict in production.

## 🧪 Testing

```bash
# Install dev dependencies
pip install pytest pytest-asyncio

# Run tests
pytest
```

## 📝 API Documentation

Interactive API docs available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file

## 🙏 Acknowledgments

- **Groq**: For ultra-fast LLM inference
- **React Flow**: For the drag-and-drop workflow builder
- **LiteLLM**: For unified LLM API
- **FastAPI**: For the backend framework

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/loolaneshailesh/agentflow-framework/issues)
- **Discussions**: [GitHub Discussions](https://github.com/loolaneshailesh/agentflow-framework/discussions)

---

**Built with ❤️ by [loolaneshailesh](https://github.com/loolaneshailesh)**
