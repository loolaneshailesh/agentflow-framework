# AgentFlow Framework

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A lightweight, open-source, modular AI agent orchestration framework built on LangGraph and LiteLLM. AgentFlow provides a clean abstraction layer for building multi-agent workflows with multi-LLM routing, dynamic tool registry, human-in-the-loop approvals, persistent memory, and full observability.

## Features

- **Workflow Orchestration** - Define, compose, and execute multi-step agent workflows using a clean spec-based API
- **Multi-LLM Routing** - Route tasks to the best LLM (OpenAI, Anthropic, Gemini, Ollama) via LiteLLM with automatic fallback
- **Dynamic Tool Registry** - Register, discover, and invoke tools at runtime with type-safe inputs and sandboxed execution
- **Human-in-the-Loop** - Built-in approval queue for sensitive operations requiring human review before proceeding
- **Persistent Memory** - Vector-backed semantic memory store for agent context and long-term recall
- **Observability** - Structured logging, trace context propagation, and execution metrics out of the box
- **Finance AP Demo** - End-to-end demo: AI-powered Finance Accounts Payable invoice exception triage workflow
- **REST API** - FastAPI-based server exposing all framework capabilities via HTTP
- **Dashboard** - Web-based frontend for monitoring workflows, agents, and approvals in real time

## Architecture

```
agentflow-framework/
├── agentflow/              # Core framework package
│   ├── core/               # Workflow, Task, Agent, Engine abstractions
│   ├── agents/             # Built-in agent implementations (ToolAgent, etc.)
│   ├── llm/                # ModelGateway - multi-LLM routing & fallback
│   ├── tools/              # Dynamic tool registry & safe code execution
│   ├── memory/             # VectorMemoryStore for semantic similarity search
│   ├── store/              # Approval queue and state persistence
│   ├── workflow/           # LangGraph-based workflow state definitions
│   ├── observability/      # Structured logging and trace context
│   ├── api/                # Pydantic schemas for REST API
│   └── utils/              # Helper utilities
├── demos/                  # Example demos (Finance AP Invoice Triage)
├── workflows/              # YAML/JSON workflow definitions
├── frontend/               # Web dashboard (HTML/CSS/JS)
├── scripts/                # Run and utility scripts
├── tests/                  # Unit and integration tests
├── .env.example            # Environment variable template
├── requirements.txt        # Python dependencies
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.9+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/loolaneshailesh/agentflow-framework.git
cd agentflow-framework

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Copy the environment template
cp .env.example .env

# Edit .env and add your API keys
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# GOOGLE_API_KEY=...
```

### Run the API Server

```bash
python scripts/run.py
# or
uvicorn agentflow.api.server:app --reload --port 8000
```

### Run the Finance AP Demo

```bash
python demos/finance_ap_demo.py
```

## Usage

### Define a Workflow

```python
from agentflow.core.workflow import Workflow
from agentflow.core.task import Task, TaskPriority
from agentflow.core.engine import WorkflowEngine
from agentflow.agents import ToolAgent

# Create an engine
engine = WorkflowEngine()

# Register an agent
agent = ToolAgent(name="MyAgent")
engine.register_agent(agent)

# Build a workflow
wf = Workflow(name="My Workflow", description="A sample workflow")
task = Task(name="Step 1", agent_id=agent.agent_id, priority=TaskPriority.HIGH)
wf.add_task(task)

# Execute
import asyncio
result = asyncio.run(engine.execute(wf))
print(result.status)
```

### Multi-LLM Routing

```python
from agentflow.llm import ModelGateway

gateway = ModelGateway()
response = await gateway.chat(
    messages=[{"role": "user", "content": "Summarize this invoice."}],
    preferred_model="gpt-4o",
    fallback_models=["claude-3-haiku", "gemini-pro"]
)
```

### Dynamic Tool Registry

```python
from agentflow.tools import ToolRegistry

registry = ToolRegistry()

@registry.register(name="fetch_invoice", description="Fetch invoice by ID")
def fetch_invoice(invoice_id: str) -> dict:
    # ... implementation
    return {"id": invoice_id, "amount": 1500.00}

result = await registry.invoke("fetch_invoice", {"invoice_id": "INV-001"})
```

### Human-in-the-Loop

```python
from agentflow.store import ApprovalQueue

queue = ApprovalQueue()
request_id = await queue.submit(
    action="approve_payment",
    payload={"vendor": "Acme Corp", "amount": 50000},
    requester="finance-agent"
)
# Request waits until a human approves or rejects via the dashboard
```

## Running Tests

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

## Finance AP Demo

The Finance Accounts Payable demo showcases an end-to-end multi-agent workflow that:

1. Ingests incoming invoices from a queue
2. Validates invoice data against PO records
3. Routes exceptions to the appropriate approval tier
4. Sends human-in-the-loop approval requests for high-value exceptions
5. Logs all decisions with full audit trail

See [`demos/finance_ap_demo.py`](demos/finance_ap_demo.py) and [`workflows/finance_ap_workflow.yaml`](workflows/finance_ap_workflow.yaml) for details.

## API Reference

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/workflows` | Create a new workflow |
| GET | `/workflows/{id}` | Get workflow status |
| POST | `/workflows/{id}/execute` | Execute a workflow |
| GET | `/agents` | List registered agents |
| POST | `/approvals/{id}/approve` | Approve a pending request |
| POST | `/approvals/{id}/reject` | Reject a pending request |

## Contributing

Contributions are welcome! Please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [LangGraph](https://github.com/langchain-ai/langgraph) - Workflow state machine engine
- [LiteLLM](https://github.com/BerriAI/litellm) - Unified LLM API interface
- [FastAPI](https://fastapi.tiangolo.com/) - High-performance REST API framework
- [Pydantic](https://docs.pydantic.dev/) - Data validation and settings management
