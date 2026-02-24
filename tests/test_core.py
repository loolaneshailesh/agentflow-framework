"""Unit tests for AgentFlow core modules."""

import asyncio
import pytest

from agentflow.core.workflow import Workflow, WorkflowStatus
from agentflow.core.task import Task, TaskStatus, TaskPriority
from agentflow.core.agent import Agent, AgentStatus
from agentflow.core.engine import WorkflowEngine


# ─── Workflow Tests ──────────────────────────────────────────────────────────

def test_workflow_creation():
    wf = Workflow(name="Test Workflow", description="A test workflow")
    assert wf.name == "Test Workflow"
    assert wf.status == WorkflowStatus.PENDING
    assert len(wf.tasks) == 0
    assert wf.workflow_id is not None


def test_workflow_add_task():
    wf = Workflow(name="Test")
    task = Task(name="Task 1")
    wf.add_task(task)
    assert len(wf.tasks) == 1


def test_workflow_to_dict():
    wf = Workflow(name="Test")
    d = wf.to_dict()
    assert d["name"] == "Test"
    assert d["status"] == "pending"
    assert "workflow_id" in d


def test_workflow_from_dict():
    data = {"name": "From Dict", "description": "Test", "max_retries": 5}
    wf = Workflow.from_dict(data)
    assert wf.name == "From Dict"
    assert wf.max_retries == 5


# ─── Task Tests ───────────────────────────────────────────────────────────────

def test_task_creation():
    task = Task(name="My Task", description="Desc")
    assert task.name == "My Task"
    assert task.status == TaskStatus.PENDING
    assert task.priority == TaskPriority.MEDIUM
    assert task.retry_count == 0


def test_task_is_ready_no_deps():
    task = Task(name="T")
    assert task.is_ready([]) is True


def test_task_is_ready_with_deps():
    task = Task(name="T", dependencies=["dep-1", "dep-2"])
    assert task.is_ready([]) is False
    assert task.is_ready(["dep-1"]) is False
    assert task.is_ready(["dep-1", "dep-2"]) is True


def test_task_lifecycle():
    task = Task(name="T")
    task.mark_running()
    assert task.status == TaskStatus.RUNNING
    task.mark_completed({"result": "ok"})
    assert task.status == TaskStatus.COMPLETED
    assert task.output_data == {"result": "ok"}


def test_task_mark_failed():
    task = Task(name="T")
    task.mark_failed("something went wrong")
    assert task.status == TaskStatus.FAILED
    assert task.error == "something went wrong"
    assert task.retry_count == 1


def test_task_can_retry():
    task = Task(name="T", max_retries=2)
    assert task.can_retry() is True
    task.mark_failed("err")
    task.mark_failed("err")
    assert task.can_retry() is False


# ─── Engine Tests ───────────────────────────────────────────────────────────

class ConcreteAgent(Agent):
    async def run(self, task, context=None):
        return {"agent": self.name, "task": task.name}


def test_engine_register_agent():
    engine = WorkflowEngine()
    agent = ConcreteAgent(name="TestAgent")
    engine.register_agent(agent)
    assert len(engine.list_agents()) == 1


def test_engine_execute_workflow():
    engine = WorkflowEngine()
    agent = ConcreteAgent(name="Worker")
    engine.register_agent(agent)

    task = Task(name="Task1", agent_id=agent.agent_id)
    wf = Workflow(name="WF")
    wf.add_task(task)

    result = asyncio.run(engine.execute(wf))
    assert result.status == WorkflowStatus.COMPLETED
    assert task.status == TaskStatus.COMPLETED
