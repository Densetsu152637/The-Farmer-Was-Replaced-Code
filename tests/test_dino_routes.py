import ast
from pathlib import Path
import random
from types import SimpleNamespace
import unittest

from test_game_language import violations


def load_dino(path="src/dino_util.py"):
    queue = {}
    exec(Path("src/queue.py").read_text(), queue)
    module = SimpleNamespace()
    namespace = module.__dict__
    namespace.update(queue=SimpleNamespace(**queue), North="N", East="E", South="S", West="W")
    tree = ast.parse(Path(path).read_text())
    tree.body = [node for node in tree.body if not isinstance(node, ast.Import)]
    exec(compile(tree, path, "exec"), namespace)
    return module


class SnakeSimulation:
    def __init__(self, size, seed, path="src/dino_util.py", initial_apple=True):
        self.size = size
        self.rng = random.Random(seed)
        self.head = (0, 0)
        self.body = []
        self.apple = self.head if initial_apple else None
        self.next_apple = None
        self.moves = 0
        self.since_food = 0
        self.max_since_food = 0
        self.dino = load_dino(path)
        d = self.dino
        d.get_world_size = lambda: size
        d.get_pos_x = lambda: self.head[0]
        d.get_pos_y = lambda: self.head[1]
        d.Entities = SimpleNamespace(Apple="apple")
        d.get_entity_type = lambda: "apple" if self.head == self.apple else None
        d.measure = self.measure
        d.move = self.move
        d.reset_dino_state()

    def measure(self):
        free = [(x, y) for x in range(self.size) for y in range(self.size)
                if (x, y) != self.head and (x, y) not in self.body]
        self.next_apple = self.rng.choice(free) if free else None
        return self.next_apple

    def move(self, direction):
        dx, dy = {"N": (0, 1), "E": (1, 0), "S": (0, -1), "W": (-1, 0)}[direction]
        target = (self.head[0] + dx, self.head[1] + dy)
        growing = self.head == self.apple
        occupied = self.body if growing else self.body[1:]
        if not (0 <= target[0] < self.size and 0 <= target[1] < self.size) or target in occupied:
            raise AssertionError("Unsafe attempted move")
        if growing:
            self.apple = self.next_apple
            self.since_food = 0
        elif self.body:
            self.body.pop(0)
        if growing or self.body or self.dino.STATE["length"] > 0:
            self.body.append(self.head)
        self.head = target
        self.moves += 1
        self.since_food += 1
        self.max_since_food = max(self.max_since_food, self.since_food)
        return True

    def run(self):
        for _ in range(self.size ** 4 + 1):
            if not self.dino.dino_walk():
                return
            assert self.dino.STATE["length"] == len(self.body)
            assert self.dino.TAIL["size"] == len(self.body)
            actual = {(x, y) for x in range(self.size) for y in range(self.size)
                      if self.dino.BODY[x][y]}
            assert actual == set(self.body)
            if self.since_food > self.size * self.size:
                raise AssertionError("Food not reached within one cycle")
        raise AssertionError("Run did not terminate")


class DinoRouteTests(unittest.TestCase):
    def test_complete_games_without_spirals(self):
        for size in (2, 4, 6, 8):
            for seed in range(20):
                with self.subTest(size=size, seed=seed):
                    sim = SnakeSimulation(size, seed)
                    sim.run()
                    self.assertEqual(len(sim.body), size * size - 1)
                    self.assertLessEqual(sim.max_since_food, size * size)

    def test_no_food_stops_after_searching_board(self):
        sim = SnakeSimulation(4, 0, initial_apple=False)
        sim.run()
        self.assertEqual(sim.moves, 16)

    def test_growth_buffer_regression(self):
        sim = SnakeSimulation(4, 112)
        sim.run()
        self.assertEqual(len(sim.body), 15)

    def test_initial_food_away_from_head_is_found(self):
        sim = SnakeSimulation(6, 7)
        sim.apple = (4, 3)
        sim.run()
        self.assertEqual(len(sim.body), 35)

    def test_cycle_visits_every_tile_once(self):
        for size in (2, 4, 6, 8, 16):
            sim = SnakeSimulation(size, 0)
            d = sim.dino
            x, y = 0, 0
            visited = set()
            for index in range(size * size):
                self.assertNotIn((x, y), visited)
                visited.add((x, y))
                self.assertEqual(d.HAM_INDEX[x][y], index)
                dx, dy = {"N": (0, 1), "E": (1, 0), "S": (0, -1), "W": (-1, 0)}[d.HAMILTONIAN[x][y]]
                x, y = x + dx, y + dy
            self.assertEqual((x, y), (0, 0))

    def test_unknown_food_only_allows_cycle_successor(self):
        sim = SnakeSimulation(4, 0)
        d = sim.dino
        self.assertTrue(d.candidate_is_safe("N", False))
        self.assertFalse(d.candidate_is_safe("E", False))

    def test_shortcut_cannot_overtake_food_even_without_tail(self):
        sim = SnakeSimulation(4, 0)
        d = sim.dino
        d.STATE["apple_x"], d.STATE["apple_y"] = (0, 2)
        self.assertFalse(d.candidate_is_safe("E", False))
        self.assertTrue(d.candidate_is_safe("N", False))

    def test_odd_boards_stop_without_building_invalid_cycle(self):
        for size in (1, 3, 5):
            sim = SnakeSimulation(size, 0)
            self.assertFalse(sim.dino.dino_walk())
            self.assertEqual(sim.moves, 0)

    def test_game_language(self):
        self.assertEqual(violations(Path("src/dino_util.py").read_text()), [])


if __name__ == "__main__":
    unittest.main()
