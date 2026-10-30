from typing import Dict, List, Any
from core.planner.exceptions import CircularDependencyError, UnknownTaskError

class DependencyResolver:
    """Resolves task dependencies and constructs the DAG execution order using Topological Sort."""

    @staticmethod
    def resolve(tasks: List[Dict[str, Any]]) -> List[str]:
        """
        Takes a list of task definitions and returns an ordered list of task IDs
        representing a valid execution sequence.
        Raises CircularDependencyError if a cycle is detected.
        Raises UnknownTaskError if a dependency does not exist.
        """
        task_map = {t["id"]: t for t in tasks}
        in_degree = {t["id"]: 0 for t in tasks}
        graph: Dict[str, List[str]] = {t["id"]: [] for t in tasks}
        
        # Build graph and in-degrees
        for task in tasks:
            task_id = task["id"]
            deps = task.get("depends_on", [])
            for dep in deps:
                if dep not in task_map:
                    raise UnknownTaskError(f"Task '{task_id}' depends on unknown task '{dep}'")
                graph[dep].append(task_id)
                in_degree[task_id] += 1
                
        # Initialize queue with nodes having 0 in-degree
        queue = [node for node in in_degree if in_degree[node] == 0]
        sorted_order = []
        
        while queue:
            node = queue.pop(0)
            sorted_order.append(node)
            
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
                    
        if len(sorted_order) != len(tasks):
            raise CircularDependencyError("Cycle detected in task dependencies!")
            
        return sorted_order
