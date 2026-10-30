import unittest
import asyncio
from core.state.models import TaskState, ContextState, EmployeeState
from core.execution.engine import ExecutionPipeline
from core.execution.registry import ToolRegistry

# Explicitly import plugins to trigger @ToolRegistry.register decorators
import core.execution.plugins.email
import core.execution.plugins.slack
import core.execution.plugins.jira
import core.execution.plugins.identity
import core.execution.plugins.calendar
import core.execution.plugins.storage

class TestExecutionAgent(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        from database import init_database
        await init_database()

    def setUp(self):
        self.employee = EmployeeState(
            id="emp-1",
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com"
        )
        self.context = ContextState(
            workflow_id="wf-test",
            employee=self.employee,
            current_task=TaskState(task_id="mock", name="mock")
        )

    async def test_plugin_loading(self):
        plugins = ToolRegistry.list_plugins()
        self.assertIn("email", plugins)
        self.assertIn("slack", plugins)
        self.assertIn("jira", plugins)

    async def test_successful_execution(self):
        task = TaskState(
            task_id="t1",
            name="Send Welcome Email",
            tool_name="email",
            input_data={"to": "jane@example.com", "subject": "Welcome!"}
        )
        
        result = await ExecutionPipeline.run(task)
        self.assertEqual(result["status"], "success")
        self.assertIn("message_id", result)

    async def test_validation_failure(self):
        # Missing 'subject' in input_data
        task = TaskState(
            task_id="t2",
            name="Send Welcome Email",
            tool_name="email",
            input_data={"to": "jane@example.com"} 
        )
        
        result = await ExecutionPipeline.run(task)
        self.assertEqual(result["status"], "failed")
        self.assertIn("Validation failed", result["error"])

    async def test_invalid_plugin(self):
        task = TaskState(
            task_id="t3",
            name="Unknown Tool Task",
            tool_name="nonexistent_tool",
            input_data={}
        )
        
        result = await ExecutionPipeline.run(task)
        self.assertEqual(result["status"], "failed")
        self.assertIn("not registered", result["error"])

    async def test_rollback(self):
        task = TaskState(
            task_id="t4",
            name="Provision Jira",
            tool_name="jira",
            input_data={"project": "IT", "summary": "Setup account"},
            output_data={"ticket_id": "IT-101"}
        )
        
        result = await ExecutionPipeline.rollback(task)
        self.assertEqual(result["status"], "success")

if __name__ == "__main__":
    unittest.main()
