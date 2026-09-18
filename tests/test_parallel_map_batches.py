import ast
from pathlib import Path
import unittest

from test_game_language import violations


SOURCE = Path("src/util.py").read_text()
FUNCTION = next(node for node in ast.parse(SOURCE).body
                if isinstance(node, ast.FunctionDef) and node.name == "parallel_map")


class ParallelMapBatchTests(unittest.TestCase):
    def run_map(self, jobs, capacity, active=1, rejected=()):
        pending = {}
        spawned = []
        joined = []
        events = []
        calls = []

        def spawn(function, bounds):
            handle = len(spawned)
            spawned.append(bounds)
            events.append("spawn")
            if handle in rejected:
                return None
            pending[handle] = (function, bounds)
            return handle

        def wait(handle):
            function, bounds = pending.pop(handle)
            joined.append(handle)
            return function(bounds)

        def worker(job):
            events.append("job")
            calls.append(job)
            return [None, False, 0, "", job][job % 5]

        namespace = {"max_drones": lambda: capacity, "num_drones": lambda: active,
                     "spawn_drone": spawn, "wait_for": wait}
        exec(compile(ast.Module(body=[FUNCTION], type_ignores=[]),
                     "src/util.py", "exec"), namespace)
        result = namespace["parallel_map"](worker, list(range(jobs)))
        self.assertEqual(result, [[None, False, 0, "", job][job % 5]
                                  for job in range(jobs)])
        self.assertEqual(sorted(calls), list(range(jobs)))
        self.assertFalse(pending, "All workers must be joined before returning")
        workers = min(jobs, max(1, capacity - active + 1))
        self.assertEqual(len(spawned), max(0, workers - 1))
        self.assertEqual(len(joined), len(spawned) - len(set(rejected) & set(range(len(spawned)))))
        self.assertEqual(events[:len(spawned)], ["spawn"] * len(spawned))
        return spawned

    def test_balanced_blocks_and_ordered_results(self):
        self.assertEqual(self.run_map(10, 4), [(0, 3), (3, 6), (6, 8)])

    def test_empty_single_and_small_inputs(self):
        for jobs in (0, 1, 2, 3):
            with self.subTest(jobs=jobs):
                self.run_map(jobs, 8)

    def test_occupied_capacity_and_single_drone(self):
        for capacity, active in ((1, 1), (8, 8), (8, 6)):
            with self.subTest(capacity=capacity, active=active):
                self.run_map(17, capacity, active)

    def test_rejected_batches_run_once_locally(self):
        self.run_map(19, 4, rejected=(0, 2))
        self.run_map(19, 4, rejected=(0, 1, 2))

    def test_many_jobs_do_not_spawn_per_job(self):
        self.run_map(1000, 4)

    def test_game_parser_subset(self):
        self.assertEqual(violations(ast.get_source_segment(SOURCE, FUNCTION)), [])


if __name__ == "__main__":
    unittest.main()
