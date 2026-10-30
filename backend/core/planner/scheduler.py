from typing import Dict, List, Any
from collections import defaultdict

class TaskScheduler:
    """Groups independent tasks into execution batches for parallel processing."""
    
    @staticmethod
    def schedule(sorted_tasks: List[str], tasks_definition: List[Dict[str, Any]]) -> List[List[str]]:
        """
        Groups tasks by execution tier.
        Tier 0 = No dependencies.
        Tier 1 = Depends on Tier 0, etc.
        Returns a list of lists, where each sublist contains tasks that can execute in parallel.
        """
        task_map = {t["id"]: t for t in tasks_definition}
        task_tiers = {}
        
        for task_id in sorted_tasks:
            deps = task_map[task_id].get("depends_on", [])
            if not deps:
                task_tiers[task_id] = 0
            else:
                max_dep_tier = max([task_tiers[d] for d in deps])
                task_tiers[task_id] = max_dep_tier + 1
                
        # Group by tier
        tier_groups = defaultdict(list)
        for task_id, tier in task_tiers.items():
            tier_groups[tier].append(task_id)
            
        # Return sorted by tier
        scheduled_batches = []
        for tier in sorted(tier_groups.keys()):
            scheduled_batches.append(tier_groups[tier])
            
        return scheduled_batches
