from typing import Dict, Any
import uuid
from core.state.models import ContextState, ExecutionPlanState, TaskPlanState, RetryState
from core.planner.validator import WorkflowValidator
from core.planner.dependency import DependencyResolver
from core.planner.priority import PriorityEngine
from core.planner.scheduler import TaskScheduler
from core.logger.structured import get_logger

logger = get_logger(__name__)

class PlanningEngine:
    """
    Coordinates validation, dependency resolution, prioritization, and scheduling 
    to generate an optimized ExecutionPlanState.
    """
    
    @staticmethod
    def generate_plan(context: ContextState, definition: Dict[str, Any]) -> ExecutionPlanState:
        logger.info(f"Generating plan for workflow {context.workflow_id}")
        
        # 1. Validation (Raises if invalid)
        WorkflowValidator.validate(context, definition)
        
        tasks_def = definition.get("tasks", [])
        
        # 2. Dependency Resolution (DAG sort)
        sorted_task_ids = DependencyResolver.resolve(tasks_def)
        
        # 3. Prioritization
        priorities = PriorityEngine.assign_priorities(tasks_def, sorted_task_ids)
        
        # 4. Scheduling (Identify parallel tiers for analytical purposes)
        # We can store the critical path or execution tiers
        scheduled_tiers = TaskScheduler.schedule(sorted_task_ids, tasks_def)
        
        # 5. Build the Execution Plan State
        plan_id = str(uuid.uuid4())
        task_plans: Dict[str, TaskPlanState] = {}

        task_map = {t["id"]: t for t in tasks_def}

        for task_id in sorted_task_ids:
            t_def = task_map[task_id]
            retry_policy = RetryState(
                max_retries=t_def.get("retry_policy", {}).get("max_retries", context.configuration.get("max_retries", 3))
            )

            task_plans[task_id] = TaskPlanState(
                task_id=task_id,
                name=t_def.get("name", task_id),
                description=t_def.get("description"),
                assigned_agent=t_def.get("agent"),
                tool_name=t_def.get("tool"),
                priority=priorities[task_id],
                dependencies=t_def.get("depends_on", []),
                estimated_duration_seconds=t_def.get("estimated_duration_seconds", 0),
                retry_policy=retry_policy,
                required_inputs=t_def.get("required_inputs", []),
                expected_outputs=t_def.get("expected_outputs", []),
                status="scheduled",
                stage=t_def.get("stage"),
                requires_approval=t_def.get("requires_approval", False),
                approval_condition=t_def.get("approval_condition", "always"),
                approval_role=t_def.get("approval_role", "hr"),
                on_failure=t_def.get("on_failure", "retry"),
                input_data=t_def.get("input", {}) or {},
            )

        # Estimated total duration: sum of the per-tier maxima, so tasks that run
        # in parallel (same tier) only count once - the slowest task in the tier.
        estimated_total_duration = 0
        for tier in scheduled_tiers:
            tier_durations = [task_plans[t_id].estimated_duration_seconds for t_id in tier if t_id in task_plans]
            if tier_durations:
                estimated_total_duration += max(tier_durations)

        plan = ExecutionPlanState(
            plan_id=plan_id,
            workflow_id=context.workflow_id,
            tasks=task_plans,
            critical_path=sorted_task_ids, # In a more complex model, this would just be the bottleneck path
            estimated_total_duration=estimated_total_duration,
            status="generated",
            template_key=definition.get("id"),
            stages=definition.get("stages", []),
        )

        logger.info(f"Successfully generated plan {plan_id} with {len(tasks_def)} tasks across {len(scheduled_tiers)} execution tiers.")
        return plan
