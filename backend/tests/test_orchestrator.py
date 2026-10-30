import unittest
import asyncio
from core.state.models import ExecutionPlanState, TaskPlanState, ContextState, EmployeeState
from core.orchestrator.execution import ExecutionManager
from core.orchestrator.retry import RetryManager
from core.agents.verification import VerificationAgent
from core.agents.execution import ExecutionAgent

class TestOrchestrator(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        from database import init_database
        await init_database()

    def setUp(self):
        self.employee = EmployeeState(
            id="emp-1",
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        from core.state.models import TaskState
        self.context = ContextState(
            workflow_id="wf-1",
            employee=self.employee,
            current_task=TaskState(task_id="mock", name="mock")
        )
        
        self.task1 = TaskPlanState(
            task_id="t1", name="Task 1", assigned_agent="VerificationAgent", status="pending"
        )
        self.task2 = TaskPlanState(
            task_id="t2", name="Task 2", assigned_agent="ExecutionAgent", tool_name="email", input_data={"to": "john@example.com", "subject": "Welcome"}, status="pending",
            dependencies=["t1"]
        )
        self.task3 = TaskPlanState(
            task_id="t3", name="Task 3", assigned_agent="ExecutionAgent", tool_name="email", input_data={"to": "john@example.com", "subject": "Welcome"}, status="pending",
            dependencies=["t1"]
        )
        
        self.plan = ExecutionPlanState(
            plan_id="plan-1",
            workflow_id="wf-1",
            tasks={"t1": self.task1, "t2": self.task2, "t3": self.task3},
            status="generated"
        )

    async def test_get_ready_tasks_initial(self):
        ready = await ExecutionManager.get_ready_tasks(self.plan)
        self.assertEqual(len(ready), 1)
        self.assertEqual(ready[0].task_id, "t1")

    async def test_get_ready_tasks_parallel(self):
        self.task1.status = "completed"
        ready = await ExecutionManager.get_ready_tasks(self.plan)
        self.assertEqual(len(ready), 2)
        ids = {t.task_id for t in ready}
        self.assertEqual(ids, {"t2", "t3"})

    async def test_retry_escalation(self):
        # Task has default max_retries = 3
        action1 = await RetryManager.handle_failure("wf-1", self.task1, "error 1")
        self.assertEqual(action1, "retry")
        self.assertEqual(self.task1.retry_policy.attempts, 1)
        
        action2 = await RetryManager.handle_failure("wf-1", self.task1, "error 2")
        self.assertEqual(action2, "retry")
        
        action3 = await RetryManager.handle_failure("wf-1", self.task1, "error 3")
        self.assertEqual(action3, "escalate")

    async def test_execution_batch(self):
        # Let's run a batch of t2 and t3 (parallel execution mock)
        self.task1.status = "completed"
        ready = await ExecutionManager.get_ready_tasks(self.plan)
        
        await ExecutionManager.execute_batch("wf-1", ready, self.context, self.plan)
        
        # After execution, they should be completed via the Mock Agents
        self.assertEqual(self.task2.status, "completed")
        self.assertEqual(self.task3.status, "completed")
        
        # Results should be injected into the context state
        self.assertIn("t2", self.context.completed_tasks_results)
        self.assertIn("t3", self.context.completed_tasks_results)

if __name__ == "__main__":
    unittest.main()
