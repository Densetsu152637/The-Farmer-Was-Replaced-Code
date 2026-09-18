import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

from test_game_language import violations


def load_functions(path, names, namespace):
    tree = ast.parse(Path(path).read_text())
    tree.body = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and (names is None or node.name in names)]
    exec(compile(tree, path, "exec"), namespace)
    return SimpleNamespace(**{node.name: namespace[node.name] for node in tree.body})


class PowerPolicyRecordTests(unittest.TestCase):
    def test_all_flowers_including_existing_ones_are_harvested_each_round(self):
        heap = load_functions("src/heap.py", None, {})
        sunflower = load_functions("src/sunflower_util.py", None, {"heap": heap})
        petals = [15, 10, 7, 15, 9, 8]
        world = {1: petals[1], 4: petals[4]}
        position = [0]
        rounds = []
        planted = []
        harvested = []
        util = SimpleNamespace(harvest_if_not=lambda entity: None,
                               till_if_required=lambda ground: None,
                               water_if_possible=lambda: None)

        def plant(entity):
            planted.append(position[0])
            world[position[0]] = petals[position[0]]

        planting = load_functions("src/planting.py", ["farm_sunflower_worker"], {
            "heap": heap, "util": util,
            "Entities": SimpleNamespace(Sunflower="sunflower"),
            "Grounds": SimpleNamespace(Soil="soil"),
            "get_entity_type": lambda: "sunflower" if position[0] in world else None,
            "plant": plant, "measure": lambda: world[position[0]],
            "get_pos_x": lambda: position[0], "get_pos_y": lambda: 0})

        def action_per_region(action, region):
            for x in region:
                position[0] = x
                action()

        def run_regions(worker):
            rounds.append([])
            # An empty worker heap must not contribute a None record.
            return [worker(region) for region in ([0, 1, 2], [], [3, 4, 5])]

        def parallel_map(worker, jobs):
            rounds[-1].append([record[0] for record in jobs])
            return [worker(job) for job in jobs]

        def harvest():
            harvested.append(position[0])
            del world[position[0]]

        def can_harvest():
            self.assertIn(position[0], world, "Stale record would wait forever")
            return True

        util.action_per_region = action_per_region
        util.run_parallel_regions = run_regions
        util.parallel_map = parallel_map
        util.go_to_coord = lambda coord: position.__setitem__(0, coord[0])
        util.lacks_item = lambda item: len(rounds) < 2
        policy = load_functions("src/policies.py", ["power_policy"], {
            "util": util, "heap": heap, "sunflower_util": sunflower,
            "planting": planting, "Items": SimpleNamespace(Power="power"),
            "can_harvest": can_harvest, "harvest": harvest})
        policy.power_policy()

        expected_batches = [[15, 15], [10], [9], [8], [7]]
        self.assertEqual(rounds, [expected_batches, expected_batches])
        self.assertEqual(sorted(harvested[:6]), list(range(6)))
        self.assertEqual(sorted(harvested[6:]), list(range(6)))
        self.assertEqual(sorted(planted[:4]), [0, 2, 3, 5])
        self.assertEqual(len(planted), 10)
        self.assertEqual(world, {})

    def test_changed_functions_follow_game_parser_subset(self):
        for path, name in (("src/policies.py", "power_policy"),
                           ("src/planting.py", "farm_sunflower_worker")):
            source = Path(path).read_text()
            node = next(node for node in ast.parse(source).body
                        if isinstance(node, ast.FunctionDef) and node.name == name)
            self.assertEqual(violations(ast.get_source_segment(source, node)), [])


if __name__ == "__main__":
    unittest.main()
