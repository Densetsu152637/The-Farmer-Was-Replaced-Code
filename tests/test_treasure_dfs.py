import ast
import copy
from pathlib import Path
import random
from types import SimpleNamespace
import unittest
from test_game_language import violations


def load(path, namespace, names=None):
    tree = ast.parse(Path(path).read_text())
    tree.body = [node for node in tree.body if not isinstance(node, ast.Import)
                 and (names is None or isinstance(node, ast.FunctionDef) and node.name in names)]
    exec(compile(tree, path, "exec"), namespace)
    return SimpleNamespace(**namespace)


class Maze:
    vectors = {"N": (0, 1), "E": (1, 0), "S": (0, -1), "W": (-1, 0)}

    def __init__(self, size, capacity, seed=0, cycles=False):
        self.size = size
        self.capacity = capacity
        self.pos = (0, 0)
        self.pending = {}
        self.next_handle = 0
        self.moves = 0
        self.gold = 0
        self.harvests = 0
        self.active = True
        self.finished = 0
        self.harvest_pending = 0
        self.treasure = (size-1, size-1)
        self.graph = {(x, y): set() for x in range(size) for y in range(size)}
        rng = random.Random(seed)
        visited = {(0, 0)}
        stack = [(0, 0)]
        while stack:
            p = stack[-1]
            neighbors = [(p[0]+dx, p[1]+dy) for dx, dy in self.vectors.values()]
            choices = [q for q in neighbors if q in self.graph and q not in visited]
            if not choices:
                stack.pop()
                continue
            q = rng.choice(choices)
            self.graph[p].add(q)
            self.graph[q].add(p)
            visited.add(q)
            stack.append(q)
        if cycles:
            for p in self.graph:
                for dx, dy in self.vectors.values():
                    q = p[0]+dx, p[1]+dy
                    if q in self.graph:
                        self.graph[p].add(q)
        self.ns = dict(North="N", East="E", South="S", West="W", util=SimpleNamespace(),
                       get_pos_x=lambda: self.pos[0], get_pos_y=lambda: self.pos[1],
                       get_world_size=lambda: size, move=self.move, can_move=self.can_move,
                       spawn_drone=self.spawn, num_drones=self.num_drones,
                       get_entity_type=lambda: ("treasure" if self.pos == self.treasure else "hedge") if self.active else "bush",
                       Entities=SimpleNamespace(Treasure="treasure", Hedge="hedge", Bush="bush"),
                       Items=SimpleNamespace(Gold="gold", Weird_Substance="substance"),
                       num_items=lambda item: self.gold, harvest=self.harvest)
        self.module = load("src/treasure_util.py", self.ns)

    def target(self, direction):
        dx, dy = self.vectors[direction]
        return ((self.pos[0]+dx) % self.size, (self.pos[1]+dy) % self.size)

    def can_move(self, direction):
        return self.target(direction) in self.graph[self.pos]

    def move(self, direction):
        self.moves += 1
        assert self.moves < 200000, "DFS did not terminate"
        if not self.can_move(direction):
            return False
        self.pos = self.target(direction)
        return True

    def spawn(self, function, *args):
        if len(self.pending) >= self.capacity-1:
            return None
        handle = self.next_handle
        self.next_handle += 1
        self.pending[handle] = (function, copy.deepcopy(args), self.pos)
        return handle

    def num_drones(self):
        if self.pending:
            self.run_worker(next(iter(self.pending)))
        return 1 + len(self.pending)

    def run_worker(self, handle):
        function, args, origin = self.pending[handle]
        parent = self.pos
        self.pos = origin
        result = function(*args)
        self.pos = parent
        del self.pending[handle]
        self.finished += 1
        return result

    def harvest(self):
        assert self.active, "Harvest after maze disappeared"
        self.harvest_pending = len(self.pending)
        assert self.pos == self.treasure
        self.active = False
        self.harvests += 1
        self.gold += 100
        return True


class TreasureDFSTests(unittest.TestCase):
    def test_parallel_and_serial_large_mazes(self):
        for size, capacity in ((1, 1), (8, 1), (8, 4), (32, 32)):
            for seed in range(4):
                with self.subTest(size=size, capacity=capacity, seed=seed):
                    maze = Maze(size, capacity, seed)
                    if seed % 2:
                        maze.pos = (size // 2, size // 2)
                    self.assertTrue(maze.module.solve_maze())
                    self.assertEqual(maze.harvests, 1)
                    self.assertFalse(maze.pending)
                    self.assertEqual(maze.finished, maze.next_handle)

    def test_nested_spawns_and_no_solution(self):
        maze = Maze(8, 8, 3)
        maze.treasure = (-1, -1)
        self.assertIsNone(maze.module.maze_branch_worker())
        self.assertEqual(maze.pos, (0, 0))
        self.assertTrue(maze.pending)
        while maze.num_drones() > 1:
            pass
        self.assertGreater(maze.finished, 1)
        self.assertEqual(maze.harvests, 0)

    def test_cyclic_maze_terminates_with_inherited_visits(self):
        maze = Maze(3, 4, cycles=True)
        self.assertTrue(maze.module.solve_maze())
        self.assertFalse(maze.pending)

    def test_blocked_first_step_and_harvest_without_progress(self):
        maze = Maze(4, 1)
        self.assertIsNone(maze.module.maze_branch_worker("S"))
        self.assertEqual(maze.pos, (0, 0))
        maze.treasure = (0, 0)
        maze.ns['harvest'] = lambda: False
        self.assertFalse(maze.module.solve_maze())
        self.assertFalse(maze.pending)

    def test_capacity_rejection_keeps_sibling_for_serial_dfs(self):
        maze = Maze(3, 1)
        maze.graph = {(0, 0): {(0, 1), (1, 0)},
                      (0, 1): {(0, 0)}, (1, 0): {(0, 0)}}
        maze.treasure = (1, 0)
        self.assertTrue(maze.module.solve_maze())
        self.assertEqual(maze.moves, 3)
        self.assertEqual(maze.next_handle, 0)

    def test_no_solution_drains_nested_workers_and_returns_false(self):
        maze = Maze(8, 4, 3)
        maze.treasure = (-1, -1)
        self.assertFalse(maze.module.solve_maze())
        self.assertFalse(maze.pending)
        self.assertGreater(maze.finished, 1)
        self.assertEqual(maze.harvests, 0)

    def test_worker_stops_on_bush_grass_or_empty_before_first_move(self):
        for entity in ("bush", "grass", None):
            maze = Maze(4, 4)
            maze.ns["get_entity_type"] = lambda: entity
            maze.module.maze_branch_worker("N")
            self.assertEqual(maze.moves, 0)
            self.assertEqual(maze.next_handle, 0)
            self.assertEqual(maze.harvests, 0)

    def test_finder_harvests_with_pending_workers_and_no_route_replay(self):
        maze = Maze(3, 3)
        maze.graph = {(0, 0): {(0, 1), (1, 0)},
                      (0, 1): {(0, 0)}, (1, 0): {(0, 0)}}
        maze.treasure = (0, 1)
        self.assertTrue(maze.module.solve_maze())
        self.assertEqual(maze.harvest_pending, 1)
        self.assertEqual(maze.moves, 1)
        self.assertEqual(maze.pos, maze.treasure)
        self.assertFalse(maze.pending)

    def test_exhausted_parent_returns_while_descendant_is_pending(self):
        maze = Maze(3, 3)
        maze.graph = {(0, 0): {(0, 1)},
                      (0, 1): {(0, 0), (0, 2), (1, 1)},
                      (0, 2): {(0, 1)}, (1, 1): {(0, 1)}}
        maze.treasure = (1, 1)
        maze.module.maze_branch_worker("N")
        self.assertEqual(maze.pos, (0, 1))
        self.assertEqual(maze.harvests, 0)
        self.assertEqual(len(maze.pending), 1)
        while maze.num_drones() > 1:
            pass
        self.assertEqual(maze.harvests, 1)

    def test_freed_slot_reused_at_later_fork(self):
        maze = Maze(3, 2)
        maze.graph = {(0, 0): {(0, 1), (1, 0)},
                      (0, 1): {(0, 0), (0, 2), (1, 1)},
                      (0, 2): {(0, 1)}, (1, 1): {(0, 1)},
                      (1, 0): {(0, 0)}}
        maze.treasure = (0, 2)
        # Complete each child during spawn, freeing the only extra slot.
        def spawn(function, *args):
            handle = maze.spawn(function, *args)
            if handle is not None:
                maze.run_worker(handle)
            return handle
        maze.ns["spawn_drone"] = spawn
        self.assertTrue(maze.module.solve_maze())
        self.assertEqual(maze.next_handle, 2)
        self.assertEqual(maze.finished, 2)

    def test_child_find_during_spawn_stops_parent_before_its_next_move(self):
        maze = Maze(3, 2)
        maze.graph = {(0, 0): {(0, 1), (1, 0)},
                      (0, 1): {(0, 0)}, (1, 0): {(0, 0)}}
        maze.treasure = (1, 0)
        def spawn(function, *args):
            handle = maze.spawn(function, *args)
            if handle is not None:
                maze.run_worker(handle)
            return handle
        maze.ns["spawn_drone"] = spawn
        self.assertTrue(maze.module.solve_maze())
        self.assertEqual(maze.moves, 1)
        self.assertEqual(maze.pos, (0, 0))

    def test_policy_repeats_only_successful_runs_until_gold_target(self):
        events = []
        gold = [0]
        def solve():
            events.append("solve")
            gold[0] += 100
            return True
        ns = dict(Items=SimpleNamespace(Gold="gold", Weird_Substance="substance", Fertilizer="fertilizer"),
                  util=SimpleNamespace(lacks_item=lambda item: item == "gold" and gold[0] < 300,
                                       has_some=lambda item: True),
                  sufficient_power=lambda: True,
                  treasure_util=SimpleNamespace(create_maze=lambda: events.append("create") or True,
                                                solve_maze=solve))
        policy = load("src/policies.py", ns, ["treasure_policy"])
        self.assertTrue(policy.treasure_policy())
        self.assertEqual(events, ["create", "solve"]*3)
        gold[0] = 0
        ns['treasure_util'].create_maze = lambda: False
        self.assertFalse(policy.treasure_policy())

    def test_creation_cost_integer_centre_and_failures(self):
        maze = Maze(5, 1)
        ns = maze.ns
        entity = [None]
        stock = [40]
        events = []
        ns.update(num_unlocked=lambda unlock: 3, Unlocks=SimpleNamespace(Mazes="mazes"),
                  num_items=lambda item: stock[0], get_entity_type=lambda: entity[0])
        ns['util'].go_to = lambda x, y: events.append((x, y))
        ns['util'].harvest_if_not = lambda e: None
        def plant(e):
            entity[0] = e
            return True
        def use(item, amount):
            events.append((item, amount))
            entity[0] = "hedge"
            return True
        ns['plant'], ns['use_item'] = plant, use
        self.assertEqual(maze.module.maze_substance_cost(), 20)
        self.assertTrue(maze.module.create_maze())
        self.assertEqual(events, [(2, 2), ("substance", 20)])
        events.clear()
        entity[0] = None
        stock[0] = 19
        self.assertFalse(maze.module.create_maze())
        self.assertEqual(events, [])

    def test_parser_subset(self):
        self.assertEqual(violations(Path("src/treasure_util.py").read_text()), [])
        source = Path("src/policies.py").read_text()
        node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == "treasure_policy")
        self.assertEqual(violations(ast.get_source_segment(source, node)), [])


if __name__ == "__main__":
    unittest.main()
