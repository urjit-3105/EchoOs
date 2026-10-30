import unittest
from core.planner.dependency import DependencyResolver
from core.planner.scheduler import TaskScheduler
from core.planner.priority import PriorityEngine
from core.planner.exceptions import CircularDependencyError, UnknownTaskError

class TestPlanner(unittest.TestCase):
    def test_dependency_resolver_valid(self):
        tasks = [
            {"id": "t1", "depends_on": []},
            {"id": "t2", "depends_on": ["t1"]},
            {"id": "t3", "depends_on": ["t2"]},
            {"id": "t4", "depends_on": ["t1"]}
        ]
        
        order = DependencyResolver.resolve(tasks)
        
        self.assertEqual("t1", order[0])
        self.assertIn("t2", order)
        self.assertIn("t3", order)
        self.assertIn("t4", order)
        self.assertTrue(order.index("t1") < order.index("t2"))
        self.assertTrue(order.index("t2") < order.index("t3"))
        self.assertTrue(order.index("t1") < order.index("t4"))

    def test_dependency_resolver_circular(self):
        tasks = [
            {"id": "t1", "depends_on": ["t2"]},
            {"id": "t2", "depends_on": ["t1"]}
        ]
        with self.assertRaises(CircularDependencyError):
            DependencyResolver.resolve(tasks)

    def test_dependency_resolver_unknown_task(self):
        tasks = [
            {"id": "t1", "depends_on": ["t99"]}
        ]
        with self.assertRaises(UnknownTaskError):
            DependencyResolver.resolve(tasks)

    def test_task_scheduler_grouping(self):
        tasks = [
            {"id": "t1", "depends_on": []},
            {"id": "t2", "depends_on": ["t1"]},
            {"id": "t3", "depends_on": ["t1"]},
            {"id": "t4", "depends_on": ["t2", "t3"]}
        ]
        
        order = DependencyResolver.resolve(tasks)
        tiers = TaskScheduler.schedule(order, tasks)
        
        self.assertEqual(len(tiers), 3)
        self.assertEqual(tiers[0], ["t1"])
        self.assertEqual(set(tiers[1]), {"t2", "t3"})
        self.assertEqual(tiers[2], ["t4"])

    def test_priority_engine(self):
        tasks = [
            {"id": "t1", "depends_on": []},
            {"id": "t2", "depends_on": ["t1"]},
            {"id": "t3", "depends_on": ["t2"]},
            {"id": "t4", "depends_on": ["t1"], "priority": 100} # override
        ]
        
        order = DependencyResolver.resolve(tasks)
        priorities = PriorityEngine.assign_priorities(tasks, order)
        
        self.assertEqual(priorities["t1"], 3)
        self.assertEqual(priorities["t2"], 1)
        self.assertEqual(priorities["t3"], 0)
        self.assertEqual(priorities["t4"], 100)

if __name__ == "__main__":
    unittest.main()
