# Contributing to AgentFlow Framework

Thank you for your interest in contributing! This document provides guidelines and steps for contributing to the AgentFlow Framework.

## Code of Conduct

This project adheres to a Contributor Code of Conduct. By participating, you are expected to uphold this code. Please be respectful and constructive in all interactions.

## How to Contribute

### Reporting Bugs

Before submitting a bug report:
1. Check the [existing issues](https://github.com/loolaneshailesh/agentflow-framework/issues) to avoid duplicates
2. Use the latest version of the framework
3. Collect relevant information (OS, Python version, error messages, stack traces)

When filing a bug report, please include:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected vs. actual behavior
- Code snippet or minimal reproducible example
- Environment details (OS, Python version, dependency versions)

### Suggesting Features

1. Open a [GitHub Issue](https://github.com/loolaneshailesh/agentflow-framework/issues/new) with the label `enhancement`
2. Describe the feature and its use case
3. Explain why this feature would be beneficial
4. If possible, outline how you would implement it

### Submitting Pull Requests

1. **Fork** the repository
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/agentflow-framework.git
   cd agentflow-framework
   ```
3. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```
4. **Set up** the development environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```
5. **Make your changes** following the coding standards below
6. **Add tests** for any new functionality
7. **Run the test suite** to make sure everything passes:
   ```bash
   pytest tests/ -v
   ```
8. **Commit** your changes with a descriptive message:
   ```bash
   git commit -m "feat: add support for parallel task execution"
   ```
9. **Push** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
10. **Open a Pull Request** from your fork to the `main` branch

## Coding Standards

### Python Style

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use [Black](https://github.com/psf/black) for code formatting:
  ```bash
  black agentflow/ tests/
  ```
- Use [flake8](https://flake8.pycqa.org/) for linting:
  ```bash
  flake8 agentflow/ tests/
  ```
- Use type hints for all function signatures
- Maximum line length: 88 characters (Black default)

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Adding or updating tests
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

Examples:
```
feat: add VectorMemoryStore with FAISS backend
fix: handle timeout in WorkflowEngine.execute()
docs: update Quick Start section in README
test: add unit tests for ModelGateway fallback
```

### Testing

- Write tests for all new features and bug fixes
- Place tests in the `tests/` directory
- Use `pytest` and `pytest-asyncio` for async tests
- Aim for meaningful test coverage of core logic
- Test file naming: `test_<module>.py`

```python
import pytest
from agentflow.core.workflow import Workflow

def test_workflow_creation():
    wf = Workflow(name="Test")
    assert wf.name == "Test"

@pytest.mark.asyncio
async def test_async_workflow_execution():
    # ...
    pass
```

### Documentation

- Add docstrings to all public classes and functions
- Use Google-style docstrings:
  ```python
  def execute(self, workflow: Workflow) -> WorkflowResult:
      """Execute a workflow and return the result.

      Args:
          workflow: The workflow to execute.

      Returns:
          A WorkflowResult containing status and output.

      Raises:
          WorkflowExecutionError: If execution fails.
      """
  ```
- Update `README.md` if your change affects usage or architecture

## Development Setup

```bash
# Clone the repo
git clone https://github.com/loolaneshailesh/agentflow-framework.git
cd agentflow-framework

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in dev mode with all dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Format code
black agentflow/ tests/

# Lint
flake8 agentflow/ tests/
```

## Project Structure

When adding new modules, follow the existing structure:

- **Core abstractions** go in `agentflow/core/`
- **Agent implementations** go in `agentflow/agents/`
- **LLM integrations** go in `agentflow/llm/`
- **Tool implementations** go in `agentflow/tools/`
- **API schemas** go in `agentflow/api/`

## Questions?

Feel free to open a [GitHub Discussion](https://github.com/loolaneshailesh/agentflow-framework/discussions) or file an issue labeled `question`.

Thank you for contributing to AgentFlow Framework!
