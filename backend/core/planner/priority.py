from typing import Dict, List, Any

class PriorityEngine:
    """Assigns priority to tasks based on dependencies and configuration rules."""
    
    @staticmethod
    def assign_priorities(tasks: List[Dict[str, Any]], sorted_order: List[str]) -> Dict[str, int]:
        """
        Calculates priority. Base priority is 0.
        Nodes that block many downstream tasks receive higher priority.
        For a simple DAG, we can assign priority inversely proportional to their depth.
        """
        priorities = {task["id"]: 0 for task in tasks}
        
        # A simple algorithm: Priority = number of descendants
        # Build descendant map
        task_map = {t["id"]: t for t in tasks}
        graph: Dict[str, List[str]] = {t["id"]: [] for t in tasks}
        
        for task in tasks:
            deps = task.get("depends_on", [])
            for dep in deps:
                if dep in graph:
                    graph[dep].append(task["id"])
                    
        # Memoize descendants
        descendants_cache = {}
        def get_descendants(node: str) -> set:
            if node in descendants_cache:
                return descendants_cache[node]
            desc = set(graph[node])
            for child in graph[node]:
                desc.update(get_descendants(child))
            descendants_cache[node] = desc
            return desc
            
        for node in priorities:
            # Base priority = number of downstream tasks depending on it
            # High impact nodes run first.
            priorities[node] = len(get_descendants(node))
            
            # Allow manual override via definition
            override = task_map[node].get("priority")
            if override is not None:
                priorities[node] = override
                
        return priorities
