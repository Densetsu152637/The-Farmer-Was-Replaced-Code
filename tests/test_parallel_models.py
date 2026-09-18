import sys
import importlib.util
import types
import unittest

sys.path.insert(0, "src")

stub_globals = types.ModuleType("globals")
stub_globals.MIN_ITEM = 0
stub_globals.TARGET_ITEMS = {}
sys.modules["globals"] = stub_globals
import util
util.spawn_drone = lambda function, args: None
util.wait_for = lambda handle: None
ORIGINAL_REGION_BOUNDS = util.region_bounds
ORIGINAL_RUN_PARALLEL = util.run_parallel_regions


def load_policies_for_tests():
    names = ["planting", "queue", "cacti_util", "dino_util"]
    for name in ["sunflower_util", "substance_util", "treasure_util", "pumpkin_util"]:
        sys.modules.pop(name, None)
    sys.modules.pop("substance_util", None)
    sys.modules.pop("treasure_util", None)
    sys.modules.pop("pumpkin_util", None)
    for name in names:
        module = types.ModuleType(name)
        if name == "queue":
            module.create_circular_queue = lambda size: {"size": 0}
        sys.modules[name] = module
    for name in ("substance_util", "treasure_util"):
        spec = importlib.util.spec_from_file_location(name, "src/" + name + ".py")
        module = importlib.util.module_from_spec(spec)
        module.North, module.East, module.South, module.West = "N", "E", "S", "W"
        sys.modules[name] = module
        spec.loader.exec_module(module)
    sys.modules.pop("policies", None)
    import policies
    return policies


class SchedulerTests(unittest.TestCase):
    def setUp(self):
        self.size = 7
        self.events = []
        util.get_world_size = lambda: self.size
        util.region_bounds = ORIGINAL_REGION_BOUNDS
        util.run_parallel_regions = ORIGINAL_RUN_PARALLEL
        util.get_pos_x = lambda: 0
        util.get_pos_y = lambda: 0
        util.wait_for = lambda handle: None
        util.go_to = lambda x, y: self.events.append(("go", x, y))
        util.move = lambda direction: None
        util.reposition = lambda: self.events.append(("reposition",))

    def test_uneven_region_bounds_are_disjoint_and_cover_all_cells(self):
        util.get_world_size = lambda: 8
        regions = util.region_bounds(4)
        cells = []
        for x0, y0, x1, y1 in regions:
            cells.extend((x, y) for x in range(x0, x1) for y in range(y0, y1))
        self.assertEqual(len(cells), len(set(cells)))
        self.assertEqual(set(cells), {(x, y) for x in range(8) for y in range(8)})
        self.assertEqual(set((r[2] - r[0], r[3] - r[1]) for r in regions), {(4, 4)})

    def test_region_bounds_uses_exact_four_by_four_blocks(self):
        util.get_world_size = lambda: 16
        regions = util.region_bounds(16)
        self.assertEqual(len(regions), 16)
        self.assertEqual(set((r[2] - r[0], r[3] - r[1]) for r in regions), {(4, 4)})

    def test_region_bounds_square_factor_rules(self):
        for size, budget, block_count, side in ((16, 8, 4, 8), (12, 9, 9, 4), (7, 16, 1, 7), (3, 100, 9, 1)):
            util.get_world_size = lambda size=size: size
            regions = util.region_bounds(budget)
            self.assertEqual(len(regions), block_count)
            self.assertEqual(set((r[2] - r[0], r[3] - r[1]) for r in regions), {(side, side)})

    def test_bounded_traversal_visits_each_owned_cell_once(self):
        seen = []
        util.action_per_tile(lambda: seen.append(True), (2, 1, 5, 4))
        self.assertEqual(len(seen), 9)

    def test_capacity_rejection_runs_inline_and_join_precedes_return(self):
        active = []
        joined = []
        util.max_drones = lambda: 2

        def spawn(worker, job):
            if len(active) == 1:
                return None
            handle = (worker, job)
            active.append(handle)
            worker(job)
            return handle

        util.spawn_drone = spawn
        util.wait_for = lambda handle: joined.append(handle)
        util.go_to = lambda x, y: None
        seen = []
        util.run_parallel_regions(lambda: seen.append(True), util.region_bounds(4))
        self.assertEqual(len(seen), 49)
        self.assertEqual(len(joined), 1)

    def test_parallel_map_preserves_order_and_falsy_results(self):
        calls = []
        joins = []
        util.max_drones = lambda: 3
        util.num_drones = lambda: 1
        util.spawn_drone = lambda function, args: None if args[0] == 1 else (function, args)
        util.wait_for = lambda handle: joins.append(handle) or handle[0](handle[1])
        def worker(value):
            calls.append(value[0])
            return [None, False, "ok"][value[0]]
        results = util.parallel_map(worker, [(0,), (1,), (2,)] )
        self.assertEqual(results, [None, False, "ok"])
        self.assertEqual(calls, [1, 2, 0])
        self.assertEqual(len(joins), 1)

    def test_actual_reset_farm_finishes_preparation_before_return(self):
        events = []
        util.change_hat = lambda hat: events.append("hat")
        util.Hats = types.SimpleNamespace(Straw_Hat="straw")
        util.max_drones = lambda: 1
        util.spawn_drone = lambda *args: None
        util.get_world_size = lambda: 2
        util.go_to = lambda x, y: events.append((x, y))
        util.get_ground_type = lambda: "soil"
        util.Grounds = types.SimpleNamespace(Soil="soil", Grassland="grass")
        util.till = lambda: None
        util.get_entity_type = lambda: None
        util.can_harvest = lambda: False
        util.plant = lambda entity: True
        util.reset_farm()
        self.assertEqual(events[0], "hat")
        self.assertEqual(len([event for event in events if isinstance(event, tuple)]), 4)

    def test_actual_simple_policies_target_exit_and_bounds(self):
        for name, plant_name in [("hay_policy", "plant_hay"), ("wood_policy", "plant_wood"), ("carrot_policy", "plant_carrot")]:
            policies = load_policies_for_tests()
            item = object()
            policies.Items = types.SimpleNamespace(Hay=item, Wood=item, Carrot=item, Power=object())
            state = {"amount": 0, "visits": 0}
            policies.util.lacks_item = lambda target, state=state: state["amount"] < 3
            policies.util.shortage_of = lambda target: False
            policies.sufficient_power = lambda: True
            def action(state=state):
                state["visits"] += 1
                state["amount"] += 1
            policies.planting = types.SimpleNamespace(**{
                plant_name: action,
                {"plant_hay": "farm_hay_tile", "plant_wood": "farm_wood_tile", "plant_carrot": "farm_carrot_tile"}[plant_name]: action,
            })
            policies.util.harvest_if = lambda: False
            policies.util.run_parallel_regions = lambda callback: (callback(), callback())
            getattr(policies, name)()
            self.assertGreaterEqual(state["amount"], 3, name)
            self.assertGreaterEqual(state["visits"], 3, name)


class PolicyModelTests(unittest.TestCase):
    def test_actual_pumpkin_worker_repairs_wrong_tile_and_waits_for_growth(self):
        policies = load_policies_for_tests()
        policies.Entities = types.SimpleNamespace(Pumpkin="pumpkin")
        state = {"entity": "empty", "ready": False, "plants": 0}
        policies.get_entity_type = lambda: state["entity"]
        policies.can_harvest = lambda: state["ready"]
        policies.harvest = lambda: None
        policies.plant = lambda entity: state.update(entity="pumpkin", plants=state["plants"] + 1) or True
        policies.util.go_to = lambda x, y: None
        policies.util.water_if_possible = lambda: None
        policies.pumpkin_util.Entities = policies.Entities
        policies.pumpkin_util.get_entity_type = policies.get_entity_type
        policies.pumpkin_util.can_harvest = policies.can_harvest
        policies.pumpkin_util.harvest = policies.harvest
        policies.pumpkin_util.plant = policies.plant
        self.assertEqual(policies.pumpkin_util.pumpkin_region((0, 0, 1, 1)), [(0, 0)])
        self.assertEqual(state["plants"], 1)
        state["ready"] = True
        self.assertEqual(policies.pumpkin_util.pumpkin_region((0, 0, 1, 1)), [])

    def test_actual_cactus_sorter_orders_rows_and_columns(self):
        spec = importlib.util.spec_from_file_location("cacti_real", "src/cacti_util.py")
        cacti_util = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cacti_util)
        cacti_util.util = util
        size = 3
        grid = [[(x * 7 + y * 3) % 10 for y in range(size)] for x in range(size)]
        pos = [0, 0]
        cacti_util.get_world_size = lambda: size
        cacti_util.util.go_to = lambda x, y: pos.__setitem__(slice(None), [x, y])
        cacti_util.measure = lambda: grid[pos[0]][pos[1]]
        def swap(direction):
            x, y = pos
            nx, ny = (x + 1, y) if direction == "E" else (x, y + 1)
            grid[x][y], grid[nx][ny] = grid[nx][ny], grid[x][y]
        cacti_util.East, cacti_util.North = "E", "N"
        cacti_util.swap = swap
        cacti_util.spawn_drone = lambda *args: None
        cacti_util.wait_for = lambda handle: None
        cacti_util.sort_cactus_grid()
        for y in range(size):
            self.assertEqual([grid[x][y] for x in range(size)], sorted(grid[x][y] for x in range(size)))
        for x in range(size):
            self.assertEqual(grid[x], sorted(grid[x]))

    def test_actual_sunflower_worker_returns_local_maximum_record(self):
        policies = load_policies_for_tests()
        policies.Entities = types.SimpleNamespace(Sunflower="sunflower")
        values = {(0, 0): 4, (0, 1): 9, (1, 0): 6, (1, 1): 1}
        pos = [0, 0]
        policies.get_pos_x = lambda: pos[0]
        policies.get_pos_y = lambda: pos[1]
        policies.get_entity_type = lambda: "sunflower"
        policies.measure = lambda: values[tuple(pos)]
        policies.sunflower_util.Entities = policies.Entities
        policies.sunflower_util.get_entity_type = policies.get_entity_type
        policies.sunflower_util.measure = policies.measure
        policies.util.go_to = lambda x, y: pos.__setitem__(slice(None), [x, y])
        self.assertEqual(policies.sunflower_util._sunflower_measure_region((0, 0, 2, 2)), [[4, [0, 0]], [9, [0, 1]], [6, [1, 0]], [1, [1, 1]]])

    def test_actual_substance_worker_fertilizes_grass_without_consuming_substance(self):
        policies = load_policies_for_tests()
        policies.Entities = types.SimpleNamespace(Grass="grass")
        policies.Grounds = types.SimpleNamespace(Grassland="grassland")
        policies.Items = types.SimpleNamespace(Fertilizer="fertilizer", Weird_Substance="weird")
        state = {"entity": "grass", "ready": True, "fertilizer": 2, "harvests": 0, "used": []}
        policies.get_entity_type = lambda: state["entity"]
        policies.can_harvest = lambda: state["ready"]
        policies.get_time = lambda: 1
        policies.num_items = lambda item: state["fertilizer"]
        policies.use_item = lambda item: state["used"].append(item) or state.update(fertilizer=state["fertilizer"] - 1) or True
        policies.harvest = lambda: state.update(harvests=state["harvests"] + 1)
        policies.util.go_to = lambda x, y: None
        policies.util.till_if_required = lambda ground: None
        policies.substance_util.Entities = policies.Entities
        policies.substance_util.Grounds = policies.Grounds
        policies.substance_util.Items = policies.Items
        for name in ("get_entity_type", "can_harvest", "get_time", "num_items", "use_item", "harvest"):
            setattr(policies.substance_util, name, getattr(policies, name))
        self.assertTrue(policies.substance_util.substance_worker((0, 0, 2, 1)))
        self.assertEqual(state["harvests"], 2)
        self.assertEqual(state["used"], ["fertilizer", "fertilizer"])

    def test_actual_substance_worker_harvests_after_last_fertilizer(self):
        policies = load_policies_for_tests()
        policies.Entities = types.SimpleNamespace(Grass="grass")
        policies.Grounds = types.SimpleNamespace(Grassland="grassland")
        policies.Items = types.SimpleNamespace(Fertilizer="fertilizer")
        state = {"fertilizer": 1, "ready": False, "time": 0, "harvests": 0}
        policies.get_entity_type = lambda: "grass"
        policies.can_harvest = lambda: state["ready"]
        policies.get_time = lambda: state.update(time=state["time"] + 1) or state["time"]
        policies.num_items = lambda item: state["fertilizer"]
        policies.use_item = lambda item: state.update(fertilizer=0, ready=True) or True
        policies.harvest = lambda: state.update(harvests=state["harvests"] + 1)
        policies.util.go_to = lambda x, y: None
        policies.util.till_if_required = lambda ground: None
        policies.substance_util.Entities = policies.Entities
        policies.substance_util.Grounds = policies.Grounds
        policies.substance_util.Items = policies.Items
        for name in ("get_entity_type", "can_harvest", "get_time", "num_items", "use_item", "harvest"):
            setattr(policies.substance_util, name, getattr(policies, name))
        self.assertTrue(policies.substance_util.substance_worker((0, 0, 1, 1)))
        self.assertEqual(state["harvests"], 1)

    def test_actual_substance_policy_runs_bounded_workers_until_target_and_joins(self):
        policies = load_policies_for_tests()
        policies.Entities = types.SimpleNamespace(Grass="grass")
        policies.Grounds = types.SimpleNamespace(Grassland="grassland")
        policies.Items = types.SimpleNamespace(Fertilizer="fertilizer", Weird_Substance="weird", Power="power")
        state = {"fertilizer": 20, "weird": 0, "used": [], "harvests": 0}
        visits = []
        handles = []
        joins = []
        policies.get_world_size = lambda: 4
        policies.max_drones = lambda: 2
        policies.util.region_bounds = lambda count: [(0, 0, 4, 2), (0, 2, 4, 4)]
        policies.util.go_to = lambda x, y: visits.append((x, y))
        policies.util.reposition = lambda: None
        policies.util.lacks_item = lambda item: state["weird"] < 5
        policies.util.has_some = lambda item: state["fertilizer"] > 0
        policies.sufficient_power = lambda: True
        policies.get_entity_type = lambda: "grass"
        policies.can_harvest = lambda: True
        policies.get_time = lambda: 1
        policies.num_items = lambda item: state["fertilizer"] if item == "fertilizer" else state["weird"]
        def use_item(item):
            state["used"].append(item)
            if item != "fertilizer" or state["fertilizer"] == 0:
                return False
            state["fertilizer"] -= 1
            return True
        policies.use_item = use_item
        policies.plant = lambda entity: True
        policies.harvest = lambda: state.update(weird=state["weird"] + 1, harvests=state["harvests"] + 1)
        policies.substance_util.Entities = policies.Entities
        policies.substance_util.Grounds = policies.Grounds
        policies.substance_util.Items = policies.Items
        for name in ("get_entity_type", "can_harvest", "get_time", "num_items", "use_item", "harvest", "plant"):
            setattr(policies.substance_util, name, getattr(policies, name))
        def spawn(worker, region):
            handle = ("h", len(handles), region)
            handles.append(handle)
            result = worker(region)
            handle_result[handle] = result
            return handle
        handle_result = {}
        policies.util.spawn_drone = spawn
        policies.util.wait_for = lambda handle: joins.append(handle) or handle_result[handle]
        policies.weird_substance_policy()
        self.assertGreaterEqual(state["weird"], 5)
        self.assertEqual(set(state["used"]), {"fertilizer"})
        self.assertEqual(len(joins), len(handles))
        self.assertTrue(all(0 <= x < 4 and 0 <= y < 4 for x, y in visits))

    def test_actual_branch_worker_finds_and_backtracks_without_harvest(self):
        policies = load_policies_for_tests()
        policies.North, policies.East, policies.South, policies.West = "N", "E", "S", "W"
        policies.Entities = types.SimpleNamespace(Treasure="treasure", Hedge="hedge")
        policies.get_pos_x = lambda: state[0]
        policies.get_pos_y = lambda: state[1]
        policies.get_entity_type = lambda: "treasure" if state == [0, 2] else "hedge"
        edges = {(0, 0): {"N": (0, 1), "E": (1, 0)}, (0, 1): {"N": (0, 2), "S": (0, 0)}, (0, 2): {"S": (0, 1)}, (1, 0): {"W": (0, 0)}}
        state = [0, 0]
        def can_move(direction):
            return direction in edges.get(tuple(state), {})
        def move(direction):
            if direction not in edges.get(tuple(state), {}):
                return False
            state[0], state[1] = edges[tuple(state)][direction]
            return True
        policies.can_move = can_move
        policies.move = move
        policies.util.spawn_drone = lambda *args: None
        policies.harvest = lambda: (_ for _ in ()).throw(AssertionError("worker harvested"))
        policies.treasure_util.North, policies.treasure_util.East = "N", "E"
        policies.treasure_util.South, policies.treasure_util.West = "S", "W"
        policies.treasure_util.Entities = policies.Entities
        for name in ("get_pos_x", "get_pos_y", "get_entity_type", "can_move", "move", "harvest"):
            setattr(policies.treasure_util, name, getattr(policies, name, None))
        result = policies.treasure_util.maze_branch_worker("N")
        self.assertEqual(result, ["N", "N"])
        self.assertIn(state, ([0, 0], [0, 1]))

    def test_actual_branch_worker_delegates_junction_and_replays_route(self):
        policies = load_policies_for_tests()
        policies.North, policies.East, policies.South, policies.West = "N", "E", "S", "W"
        policies.Entities = types.SimpleNamespace(Treasure="treasure", Hedge="hedge")
        state = [0, 0]
        edges = {(0, 0): {"N": (0, 1)}, (0, 1): {"N": (0, 2), "E": (1, 1), "W": (-1, 1)}, (0, 2): {"S": (0, 1)}, (1, 1): {"E": (2, 1), "W": (0, 1)}, (2, 1): {"W": (1, 1)}, (-1, 1): {"E": (0, 1)}}
        policies.get_pos_x = lambda: state[0]
        policies.get_pos_y = lambda: state[1]
        policies.get_entity_type = lambda: "treasure" if state == [2, 1] else "hedge"
        policies.can_move = lambda direction: direction in edges.get(tuple(state), {})
        policies.move = lambda direction: state.__setitem__(slice(None), list(edges[tuple(state)][direction])) or True if direction in edges.get(tuple(state), {}) else False
        policies.harvest = lambda: (_ for _ in ()).throw(AssertionError("worker harvested"))
        handles = []
        results = {}
        def spawn(worker, direction):
            handle = len(handles)
            handles.append(handle)
            caller = list(state)
            results[handle] = worker(direction)
            state[0], state[1] = caller
            return handle
        policies.spawn_drone = spawn
        policies.wait_for = lambda handle: results[handle]
        policies.treasure_util.North, policies.treasure_util.East = "N", "E"
        policies.treasure_util.South, policies.treasure_util.West = "S", "W"
        policies.treasure_util.Entities = policies.Entities
        for name in ("get_pos_x", "get_pos_y", "get_entity_type", "can_move", "move", "spawn_drone", "wait_for"):
            setattr(policies.treasure_util, name, getattr(policies, name, None))
        route = policies.treasure_util.maze_branch_worker("N")
        self.assertEqual(route, ["N", "E", "E"])
        self.assertIn(state, ([0, 0], [0, 1]))
        self.assertTrue(handles)

    def test_actual_treasure_policy_joins_workers_then_harvests_once(self):
        policies = load_policies_for_tests()
        policies.North, policies.East, policies.South, policies.West = "N", "E", "S", "W"
        policies.Entities = types.SimpleNamespace(Treasure="treasure", Bush="bush")
        policies.Grounds = types.SimpleNamespace(Soil="soil")
        policies.Items = types.SimpleNamespace(Weird_Substance="substance")
        policies.get_world_size = lambda: 4
        policies.num_unlocked = lambda unlock: 2
        policies.Unlocks = types.SimpleNamespace(Mazes="mazes")
        events = []
        policies.util.reposition = lambda: events.append("reposition")
        policies.util.harvest_if = lambda: False
        policies.util.till_if_required = lambda ground: None
        policies.plant = lambda entity: events.append("plant") or True
        policies.use_item = lambda item, amount: events.append(("use", amount)) or True
        policies.can_move = lambda direction: True
        policies.treasure_util.maze_branch_worker = lambda direction: events.append(("worker", direction)) or [direction]
        handles = []
        policies.util.spawn_drone = lambda worker, direction: handles.append(direction) or direction
        policies.util.wait_for = lambda handle: events.append(("join", handle)) or [handle]
        policies.move = lambda direction: events.append(("move", direction)) or True
        policies.get_entity_type = lambda: "treasure"
        policies.harvest = lambda: events.append("harvest")
        self.assertTrue(policies.treasure_policy())
        self.assertEqual([e for e in events if e == "harvest"], ["harvest"])
        self.assertTrue(all(e[0] == "join" for e in events if isinstance(e, tuple) and e[0] == "join"))
        self.assertEqual([e for e in events if isinstance(e, tuple) and e[0] == "use"], [("use", 8)])

    def test_worker_isolation_keeps_parent_sunflower_heap_until_merge(self):
        policies = load_policies_for_tests()
        policies.Entities = types.SimpleNamespace(Sunflower="sunflower")
        policies.get_entity_type = lambda: "sunflower"
        policies.measure = lambda: 17
        policies.sunflower_util.Entities = policies.Entities
        policies.sunflower_util.get_entity_type = policies.get_entity_type
        policies.sunflower_util.measure = policies.measure
        policies.util.go_to = lambda x, y: None
        policies.sunflower_util.known_petals = policies.heap.create_heap()
        parent_heap = policies.sunflower_util.known_petals

        # A drone receives a copied callback context. Running the real worker
        # must return data and leave parent-owned reduction state untouched.
        worker_result = policies.sunflower_util._sunflower_measure_region((0, 0, 1, 1))
        self.assertEqual(worker_result, [[17, [0, 0]]])
        self.assertIs(policies.sunflower_util.known_petals, parent_heap)
        self.assertEqual(parent_heap["size"], 0)

        # Only the parent performs the explicit merge.
        policies.heap.heap_push(parent_heap, worker_result[0], lambda item: item[0])
        self.assertEqual(parent_heap["size"], 1)

    def test_worker_planting_does_not_call_parent_heap_helper(self):
        policies = load_policies_for_tests()
        spec = importlib.util.spec_from_file_location("planting_isolated", "src/planting.py")
        planting = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(planting)
        planting.util = policies.util
        planting.sunflower_util = policies.sunflower_util
        planting.Entities = types.SimpleNamespace(Sunflower="sunflower")
        planting.Grounds = types.SimpleNamespace(Soil="soil")
        planting.get_entity_type = lambda: None
        planting.util.harvest_if_not = lambda entity: None
        planting.util.till_if_required = lambda ground: None
        planting.plant = lambda entity: True
        planting.sunflower_util.known_petals = policies.heap.create_heap()
        parent_heap = planting.sunflower_util.known_petals
        planting.plant_sunflower_worker()
        self.assertEqual(parent_heap["size"], 0)

    def test_dinosaur_preparation_uses_bounded_regions(self):
        regions = [(0, 0, 4, 2), (0, 2, 4, 4)]
        touched = {(x, y) for r in regions for x in range(r[0], r[2]) for y in range(r[1], r[3])}
        self.assertEqual(len(touched), 16)

    def test_dinosaur_policy_stops_after_nonproductive_run(self):
        policies = load_policies_for_tests()
        policies.Items = types.SimpleNamespace(Bone="bone", Cactus="cactus", Power="power")
        policies.Hats = types.SimpleNamespace(Dinosaur_Hat="dino", Straw_Hat="straw")
        policies.util.lacks_item = lambda item: item == "bone"
        policies.util.shortage_of = lambda item: False
        policies.sufficient_power = lambda: True
        policies.num_items = lambda item: 0
        policies.change_hat = lambda hat: None
        policies.dino_util.reset_dino_state = lambda: None
        calls = []
        policies.dino_util.dino_walk = lambda: calls.append(True) and False
        policies.util.reset_farm = lambda: None
        self.assertFalse(policies.dinosaur_policy())
        self.assertEqual(len(calls), 1)

    def test_dinosaur_policy_repeats_only_after_bone_progress(self):
        policies = load_policies_for_tests()
        policies.Items = types.SimpleNamespace(Bone="bone", Cactus="cactus", Power="power")
        policies.Hats = types.SimpleNamespace(Dinosaur_Hat="dino", Straw_Hat="straw")
        state = {"bone": 0, "runs": 0}
        policies.util.lacks_item = lambda item: state["bone"] < 2
        policies.util.shortage_of = lambda item: False
        policies.sufficient_power = lambda: True
        policies.num_items = lambda item: state["bone"]
        policies.change_hat = lambda hat: state.update(bone=state["bone"] + (1 if hat == "straw" else 0))
        policies.dino_util.reset_dino_state = lambda: None
        policies.dino_util.dino_walk = lambda: False
        policies.util.reset_farm = lambda: None
        self.assertFalse(policies.dinosaur_policy())
        self.assertEqual(state["bone"], 2)

    def test_pumpkin_pending_worker_scans_only_pending_and_retries_dead_tile(self):
        policies = load_policies_for_tests()
        policies.Entities = types.SimpleNamespace(Pumpkin="pumpkin")
        state = {"coord": None, "attempts": {(1, 1): 0}, "visits": []}
        policies.util.go_to = lambda x, y: (state.update(coord=(x, y)), state["visits"].append((x, y)))
        policies.pumpkin_util.util.go_to = policies.util.go_to
        policies.get_entity_type = lambda: "pumpkin"
        policies.can_harvest = lambda: state["attempts"].get(state["coord"], 0) > 0
        policies.pumpkin_util.Entities = policies.Entities
        policies.pumpkin_util.get_entity_type = policies.get_entity_type
        policies.pumpkin_util.can_harvest = policies.can_harvest
        result = policies.pumpkin_util.pumpkin_pending_region([(1, 1), (2, 2)])
        self.assertEqual(state["visits"], [(1, 1), (2, 2)])
        self.assertEqual(result, [(1, 1), (2, 2)])
        state["attempts"][(1, 1)] = 1
        result = policies.pumpkin_util.pumpkin_pending_region([(1, 1), (2, 2)])
        self.assertEqual(state["visits"], [(1, 1), (2, 2), (1, 1), (2, 2)])
        self.assertEqual(result, [(2, 2)])
        self.assertEqual(len(state["visits"]), 4)

    def test_power_policy_stops_heap_when_target_reached(self):
        policies = load_policies_for_tests()
        policies.Items = types.SimpleNamespace(Power="power")
        policies.planting.plant_sunflower_worker = lambda: None
        policies.util.run_parallel_regions = lambda action: None
        policies.util.lacks_item = lambda item: False
        policies.sunflower_util._sunflower_measure_regions = lambda: [[9, [0, 0]], [8, [1, 0]], [1, [2, 0]]]
        harvested = []
        policies.sunflower_util.known_petals = policies.heap.create_heap()
        policies.sunflower_util.get_end = lambda: policies.heap.heap_pop(policies.sunflower_util.known_petals)
        policies.util.go_to_coord = lambda coord: None
        policies.can_harvest = lambda: True
        policies.harvest = lambda: harvested.append(True)
        remaining = iter([True, True, False])
        policies.util.lacks_item = lambda item: next(remaining, False)
        policies.power_policy()
        self.assertEqual(len(harvested), 1)
        util.lacks_item = lambda item: True


if __name__ == "__main__":
    unittest.main()

