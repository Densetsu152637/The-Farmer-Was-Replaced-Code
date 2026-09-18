import sys
import types
import unittest
import random
import importlib
import threading

sys.path.insert(0, "src")
sys.path.insert(0, "tests")

from test_parallel_models import load_policies_for_tests

def fresh_policies():
    # The shared loader installs lightweight dependency modules.  Remove every
    # policy dependency first so each test gets a clean import graph; reloading
    # only ``policies`` leaves stale util/heap state behind.
    for name in ("policies", "planting", "queue", "sunflower_util", "pumpkin_util", "cacti_util",
                 "substance_util", "treasure_util", "dino_util"):
        sys.modules.pop(name, None)
    sys.modules.pop("util", None)
    return load_policies_for_tests()


def _run_capture(function, errors):
    try:
        function()
    except BaseException as error:
        errors.append(error)


class CropPolicyIntegrationTests(unittest.TestCase):
    def tearDown(self):
        for name in ("policies", "planting", "queue", "sunflower_util", "pumpkin_util", "cacti_util",
                     "substance_util", "treasure_util", "dino_util", "util"):
            sys.modules.pop(name, None)

    def test_pumpkin_policy_joins_all_readiness_rounds_before_global_harvest(self):
        policies = fresh_policies()
        policies.Entities = types.SimpleNamespace(Pumpkin="pumpkin")
        policies.Items = types.SimpleNamespace(Pumpkin="pumpkin", Carrot="carrot", Power="power")
        lacks_calls = [0]
        def lacks_item(item):
            lacks_calls[0] += 1
            return lacks_calls[0] == 1
        policies.util.lacks_item = lacks_item
        policies.util.shortage_of = lambda item: False
        policies.util.run_parallel_regions = lambda action: None
        policies.planting.plant_pumpkin = lambda: None
        policies.util.region_bounds = lambda count: [(0, 0, 1, 1), (1, 0, 2, 1)]
        policies.max_drones = lambda: 2
        policies.util.reposition = lambda: None
        events = []
        policies.harvest = lambda: events.append("harvest")
        wait_calls = [0]
        handles = []
        policies.util.spawn_drone = lambda worker, region: (worker, region)
        def wait_for(handle):
            handles.append(handle[1])
            wait_calls[0] += 1
            return wait_calls[0] > 2
        policies.util.wait_for = wait_for
        rounds = iter([[], [], [], []])
        policies.pumpkin_util.pumpkin_region = lambda region: next(rounds)
        policies.pumpkin_policy()
        self.assertEqual(len(handles), 2)
        self.assertEqual(events, ["harvest"])

    def test_pumpkin_policy_target_transition_completes_without_hanging(self):
        policies = fresh_policies()
        policies.Entities = types.SimpleNamespace(Pumpkin="pumpkin")
        policies.Items = types.SimpleNamespace(Pumpkin="pumpkin", Carrot="carrot", Power="power")
        remaining = iter([True, True, True, False])
        policies.util.lacks_item = lambda item: next(remaining, False)
        policies.util.shortage_of = lambda item: False
        policies.util.run_parallel_regions = lambda action: None
        policies.planting.plant_pumpkin = lambda: None
        policies.util.region_bounds = lambda count: [(0, 0, 1, 1)]
        policies.max_drones = lambda: 1
        policies.util.reposition = lambda: None
        policies.harvest = lambda: None
        policies.util.spawn_drone = lambda worker, region: (worker, region)
        policies.util.wait_for = lambda handle: handle[0](handle[1])
        calls = [0]
        def worker(region):
            calls[0] += 1
            return calls[0] > 1
        policies.pumpkin_util.pumpkin_region = worker
        # This bounded runner turns the current readiness-loop regression into
        # a deterministic failure instead of letting the suite hang forever.
        error = []
        thread = threading.Thread(target=lambda: _run_capture(policies.pumpkin_policy, error), daemon=True)
        thread.start()
        thread.join(1.0)
        self.assertFalse(thread.is_alive(), "pumpkin_policy did not exit after readiness became true")
        self.assertEqual(error, [])

    def test_pumpkin_regions_join_and_repair_dead_wrong_and_empty_tiles(self):
        policies = fresh_policies()
        policies.Entities = types.SimpleNamespace(Pumpkin="pumpkin", Dead_Pumpkin="dead")
        policies.util.go_to = lambda x, y: None
        policies.util.water_if_possible = lambda: None
        states = iter(["dead", "empty", "carrot", "pumpkin"])
        planted = []
        policies.get_entity_type = lambda: next(states)
        policies.harvest = lambda: None
        policies.plant = lambda entity: planted.append(entity) or True
        policies.can_harvest = lambda: True
        policies.pumpkin_util.Entities = policies.Entities
        policies.pumpkin_util.get_entity_type = policies.get_entity_type
        policies.pumpkin_util.harvest = policies.harvest
        policies.pumpkin_util.plant = policies.plant
        policies.pumpkin_util.can_harvest = policies.can_harvest
        self.assertEqual(policies.pumpkin_util.pumpkin_region((0, 0, 1, 4)), [(0, 0), (0, 1), (0, 2)])
        self.assertEqual(planted, ["pumpkin", "pumpkin", "pumpkin"])

    def test_sunflower_measure_region_returns_highest_coordinate(self):
        policies = fresh_policies()
        policies.Entities = types.SimpleNamespace(Sunflower="sunflower")
        pos = [0, 0]
        values = {(0, 0): 2, (0, 1): 9, (1, 0): 5, (1, 1): 7}
        policies.util.go_to = lambda x, y: pos.__setitem__(slice(None), [x, y])
        policies.get_pos_x = lambda: pos[0]
        policies.get_pos_y = lambda: pos[1]
        policies.get_entity_type = lambda: "sunflower"
        policies.measure = lambda: values[tuple(pos)]
        policies.sunflower_util.Entities = policies.Entities
        policies.sunflower_util.get_entity_type = policies.get_entity_type
        policies.sunflower_util.measure = policies.measure
        self.assertEqual(
            policies.sunflower_util._sunflower_measure_region((0, 0, 2, 2)),
            [[2, [0, 0]], [9, [0, 1]], [5, [1, 0]], [7, [1, 1]]],
        )

    def test_power_policy_harvests_every_worker_record(self):
        policies = fresh_policies()
        policies.Items = types.SimpleNamespace(Power="power")
        remaining = iter([True, True, True, False])
        policies.util.lacks_item = lambda item: next(remaining, False)
        policies.planting.plant_sunflower_worker = lambda: None
        policies.util.run_parallel_regions = lambda action: None
        policies.sunflower_util.known_petals = {"size": 0}
        records = iter([ [9, [0, 1]], [7, [1, 1]] ])
        policies.sunflower_util._sunflower_measure_regions = lambda: list(records)
        policies.sunflower_util.known_petals = {"size": 0}
        policies.sunflower_util.get_end = lambda: policies.heap.heap_pop(policies.sunflower_util.known_petals)
        policies.util.go_to_coord = lambda coord: None
        policies.can_harvest = lambda: True
        harvested = []
        policies.harvest = lambda: harvested.append(True)
        policies.power_policy()
        self.assertEqual(len(harvested), 2)

    def test_sunflower_regions_flattens_inline_and_spawned_records(self):
        policies = fresh_policies()
        policies.max_drones = lambda: 2
        policies.sunflower_util.max_drones = policies.max_drones
        policies.sunflower_util.Entities = types.SimpleNamespace(Sunflower="sunflower")
        policies.util.region_bounds = lambda count: [(0, 0, 1, 1), (1, 0, 2, 1)]
        policies.util.reposition = lambda: None
        policies.sunflower_util._sunflower_measure_region = lambda region: [[region[0] + 1, [region[0], 0]]]
        calls = [0]
        policies.util.spawn_drone = lambda worker, region: None if calls.__setitem__(0, calls[0] + 1) is None and calls[0] == 1 else (worker, region)
        policies.util.wait_for = lambda handle: handle[0](handle[1])
        self.assertEqual(
            policies.sunflower_util._sunflower_measure_regions(),
            [[1, [0, 0]], [2, [1, 0]]],
        )

    def test_pumpkin_failure_joins_already_accepted_workers(self):
        policies = fresh_policies()
        policies.Entities = types.SimpleNamespace(Pumpkin="pumpkin")
        policies.Items = types.SimpleNamespace(Pumpkin="pumpkin", Carrot="carrot", Power="power")
        policies.util.lacks_item = lambda item: True
        policies.util.shortage_of = lambda item: False
        policies.util.run_parallel_regions = lambda action: None
        policies.planting.plant_pumpkin = lambda: None
        policies.util.region_bounds = lambda count: [(0, 0, 1, 1), (1, 0, 2, 1)]
        policies.max_drones = lambda: 2
        joined = []
        handles = [("accepted",)]
        policies.util.spawn_drone = lambda worker, region: handles.pop(0) if handles else None
        policies.util.wait_for = lambda handle: joined.append(handle) or True
        policies.pumpkin_util.pumpkin_region = lambda region: None if region == (1, 0, 2, 1) else True
        self.assertFalse(policies.pumpkin_policy())
        self.assertEqual(joined, [("accepted",)])

    def test_cactus_sorter_joins_row_and_column_phases(self):
        spec = __import__("importlib.util").util.spec_from_file_location("cacti_integration", "src/cacti_util.py")
        cacti = __import__("importlib.util").util.module_from_spec(spec)
        spec.loader.exec_module(cacti)
        size = 3
        grid = [[(x * 5 + y * 7) % 10 for y in range(size)] for x in range(size)]
        pos = [0, 0]
        cacti.get_world_size = lambda: size
        cacti.util.go_to = lambda x, y: pos.__setitem__(slice(None), [x, y])
        cacti.measure = lambda: grid[pos[0]][pos[1]]
        cacti.East, cacti.North = "E", "N"
        def swap(direction):
            x, y = pos
            nx, ny = (x + 1, y) if direction == "E" else (x, y + 1)
            grid[x][y], grid[nx][ny] = grid[nx][ny], grid[x][y]
        cacti.swap = swap
        joined = []
        cacti.util.spawn_drone = lambda *args: args
        def wait_for(handle):
            joined.append(handle)
            handle[0](*handle[1:])
        cacti.util.wait_for = wait_for
        cacti.sort_cactus_grid()
        self.assertTrue(joined)
        for y in range(size):
            self.assertEqual([grid[x][y] for x in range(size)], sorted(grid[x][y] for x in range(size)))
        for x in range(size):
            self.assertEqual([grid[x][y] for y in range(size)], sorted(grid[x][y] for y in range(size)))

    def test_cactus_sorter_multiple_sizes_and_seeds(self):
        for size in (1, 2, 3, 8):
            for seed in range(3):
                random.seed(seed)
                spec = __import__("importlib.util").util.spec_from_file_location("cacti_seeded", "src/cacti_util.py")
                cacti = __import__("importlib.util").util.module_from_spec(spec)
                spec.loader.exec_module(cacti)
                grid = [[random.randrange(10) for _ in range(size)] for _ in range(size)]
                pos = [0, 0]
                cacti.get_world_size = lambda: size
                cacti.util.go_to = lambda x, y: pos.__setitem__(slice(None), [x, y])
                cacti.measure = lambda: grid[pos[0]][pos[1]]
                cacti.East, cacti.North = "E", "N"
                def swap(direction):
                    x, y = pos
                    nx, ny = (x + 1, y) if direction == "E" else (x, y + 1)
                    grid[x][y], grid[nx][ny] = grid[nx][ny], grid[x][y]
                cacti.swap = swap
                cacti.util.spawn_drone = lambda *args: None
                cacti.util.wait_for = lambda handle: None
                cacti.sort_cactus_grid()
                for x in range(size):
                    self.assertEqual([grid[x][y] for y in range(size)], sorted(grid[x][y] for y in range(size)), (size, seed, x, grid))


if __name__ == "__main__":
    unittest.main()
