"""Safe Python code execution tool for AgentFlow agents."""

from __future__ import annotations

import ast
import io
import logging
import sys
import traceback
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from agentflow.tools.base import BaseTool

logger = logging.getLogger(__name__)

# Dangerous builtins to block in sandboxed execution
_BLOCKED_BUILTINS = {
    "__import__", "eval", "exec", "compile", "open",
    "input", "breakpoint", "__loader__", "__spec__",
}


@dataclass
class CodeExecutorTool(BaseTool):
    """Tool for safely executing Python code snippets."""

    name: str = "code_executor"
    description: str = "Execute Python code and return the output."
    timeout_seconds: int = 30
    allowed_imports: List[str] = field(default_factory=lambda: [
        "math", "json", "re", "datetime", "collections",
        "itertools", "functools", "string", "random",
    ])
    sandbox_mode: bool = True

    async def arun(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code asynchronously (runs in executor to avoid blocking)."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.run, inputs)

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code synchronously and capture output."""
        code = inputs.get("code") or inputs.get("input") or ""
        if not code.strip():
            return {"error": "No code provided", "output": "", "success": False}

        logger.info(f"CodeExecutorTool executing {len(code)} chars of code")

        # Validate syntax first
        try:
            ast.parse(code)
        except SyntaxError as e:
            return {"error": f"SyntaxError: {e}", "output": "", "success": False}

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()

        try:
            local_vars: Dict[str, Any] = {}
            global_vars: Dict[str, Any] = {"__builtins__": self._get_safe_builtins()}

            with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
                exec(compile(code, "<agentflow>", "exec"), global_vars, local_vars)

            output = stdout_buf.getvalue()
            stderr_output = stderr_buf.getvalue()

            return {
                "success": True,
                "output": output,
                "stderr": stderr_output,
                "locals": {k: repr(v) for k, v in local_vars.items() if not k.startswith("_")},
                "error": None,
            }

        except Exception as e:
            tb = traceback.format_exc()
            return {
                "success": False,
                "output": stdout_buf.getvalue(),
                "error": str(e),
                "traceback": tb,
            }

    def _get_safe_builtins(self) -> Dict[str, Any]:
        """Return a filtered set of builtins safe for sandboxed execution."""
        if not self.sandbox_mode:
            return __builtins__ if isinstance(__builtins__, dict) else vars(__builtins__)

        safe = {}
        all_builtins = __builtins__ if isinstance(__builtins__, dict) else vars(__builtins__)
        for name, val in all_builtins.items():
            if name not in _BLOCKED_BUILTINS:
                safe[name] = val

        # Allow only safe imports
        original_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __import__

        def safe_import(name, *args, **kwargs):
            if name not in self.allowed_imports:
                raise ImportError(f"Import '{name}' is not allowed in sandbox mode")
            return original_import(name, *args, **kwargs)

        safe["__import__"] = safe_import
        return safe
