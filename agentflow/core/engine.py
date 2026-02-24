"""Workflow execution engine for AgentFlow."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from agentflow.core.task import Task, TaskStatus
from agentflow.core.workflow import Workflow, WorkflowStatus

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Executes workflows by scheduling and running tasks with agents."""

    def __init__(self) -> None:
        self._agents: Dict[str, Any] = {}
        self._running_workflows: Dict[str, Workflow] = {}
        self._completed_task_ids: List[str] = []

    def register_agent(self, agent: Any) -> None:
        """Register an agent with the engine."""
        self._agents[agent.agent_id] = agent
        logger.info(f"Registered agent: {agent.name} ({agent.agent_id})")

    async def execute(self, workflow: Workflow, context: Optional[Dict[str, Any]] = None) -> Workflow:
        """Execute a workflow, running all tasks in dependency order."""
        context = context or {}
        workflow.status = WorkflowStatus.RUNNING
        self._running_workflows[workflow.workflow_id] = workflow
        self._completed_task_ids = []

        logger.info(f"Starting workflow: {workflow.name} ({workflow.workflow_id})")

        try:
            pending_tasks = list(workflow.tasks)
            max_iterations = len(pending_tasks) * 2  # prevent infinite loops
            iteration = 0

            while pending_tasks and iteration < max_iterations:
                iteration += 1
                ready_tasks = [
                    t for t in pending_tasks
                    if t.is_ready(self._completed_task_ids)
                    and t.status == TaskStatus.PENDING
                ]

                if not ready_tasks:
                    logger.warning("No ready tasks found - possible circular dependency")
                    break

                # Execute ready tasks concurrently
                await asyncio.gather(
                    *[self._execute_task(task, context) for task in ready_tasks],
                    return_exceptions=True
                )

                # Remove completed/failed tasks from pending
                pending_tasks = [
                    t for t in pending_tasks
                    if t.status == TaskStatus.PENDING
                ]

            failed_tasks = [t for t in workflow.tasks if t.status == TaskStatus.FAILED]
            if failed_tasks:
                workflow.status = WorkflowStatus.FAILED
                logger.error(f"Workflow {workflow.name} failed - {len(failed_tasks)} tasks failed")
            else:
                workflow.status = WorkflowStatus.COMPLETED
                logger.info(f"Workflow {workflow.name} completed successfully")

        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            logger.exception(f"Workflow {workflow.name} crashed: {e}")

        finally:
            self._running_workflows.pop(workflow.workflow_id, None)

        return workflow

    async def _execute_task(self, task: Task, context: Dict[str, Any]) -> None:
        """Execute a single task using its assigned agent."""
        task.mark_running()
        logger.info(f"Executing task: {task.name} ({task.task_id})")

        try:
            agent = self._agents.get(task.agent_id)
            if agent is None:
                raise ValueError(f"No agent found with id: {task.agent_id}")

            result = await asyncio.wait_for(
                agent.run(task, context),
                timeout=task.timeout_seconds
            )

            task.mark_completed(result if isinstance(result, dict) else {"result": result})
            self._completed_task_ids.append(task.task_id)
            logger.info(f"Task completed: {task.name}")

        except asyncio.TimeoutError:
            error_msg = f"Task {task.name} timed out after {task.timeout_seconds}s"
            task.mark_failed(error_msg)
            logger.error(error_msg)

        except Exception as e:
            task.mark_failed(str(e))
            logger.error(f"Task {task.name} failed: {e}")

    def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowStatus]:
        """Get the current status of a running workflow."""
        workflow = self._running_workflows.get(workflow_id)
        return workflow.status if workflow else None

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents."""
        return [agent.to_dict() for agent in self._agents.values()]
