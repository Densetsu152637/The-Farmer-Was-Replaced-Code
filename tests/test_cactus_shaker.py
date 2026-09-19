import ast
from pathlib import Path
from types import SimpleNamespace
import itertools
import random
import unittest
from test_game_language import violations


class Grid:
    directions = {"E": (1, 0), "W": (-1, 0), "N": (0, 1), "S": (0, -1)}

    def __init__(self, n):
        self.n = n
        self.cells = {(x, y): 0 for x in range(n) for y in range(n)}
        self.pos = (0, 0)
        self.reads = []
        self.moves = 0
        self.swaps = 0
        tree = ast.parse(Path("src/cacti_util.py").read_text())
        tree.body = [node for node in tree.body if not isinstance(node, ast.Import)]
        self.ns = dict(East="E", West="W", North="N", South="S",
                       get_world_size=lambda: n, measure=self.measure,
                       move=self.move, swap=self.swap,
                       util=SimpleNamespace(go_to=self.go_to,
                                            parallel_map=lambda f, jobs: [f(job) for job in jobs]))
        exec(compile(tree, "src/cacti_util.py", "exec"), self.ns)

    def go_to(self, x, y):
        assert (x, y) in self.cells
        self.pos = (x, y)

    def neighbor(self, direction):
        dx, dy = self.directions[direction]
        p = (self.pos[0] + dx, self.pos[1] + dy)
        assert p in self.cells, "Sorter crossed a boundary"
        return p

    def measure(self, direction=None):
        p = self.neighbor(direction) if direction else self.pos
        self.reads.append(p)
        return self.cells[p]

    def move(self, direction):
        self.pos = self.neighbor(direction)
        self.moves += 1
        return True

    def swap(self, direction):
        p = self.neighbor(direction)
        self.cells[p], self.cells[self.pos] = self.cells[self.pos], self.cells[p]
        self.swaps += 1
        return True


class CactusShakerTests(unittest.TestCase):
    def check_line(self, values, direction):
        g = Grid(len(values) + 2)
        dx, dy = g.directions[direction]
        start = (1, 1)
        if direction == "W": start = (len(values), 1)
        if direction == "S": start = (1, len(values))
        coords = [(start[0] + dx*i, start[1] + dy*i) for i in range(len(values))]
        for p, value in zip(coords, values): g.cells[p] = value
        before = g.cells.copy()
        self.assertTrue(g.ns["shaker_sort"](start, len(values), direction))
        self.assertEqual([g.cells[p] for p in coords], sorted(values, reverse=direction in ("W", "S")))
        self.assertTrue(all(g.cells[p] == v for p, v in before.items() if p not in coords))
        self.assertTrue(all(p in coords for p in g.reads))
        return g

    def test_all_directions_and_duplicate_values(self):
        for direction in Grid.directions:
            for values in itertools.product(range(3), repeat=4):
                self.check_line(values, direction)
            for values in ([], [5], list(range(32)), list(range(31, -1, -1))):
                self.check_line(values, direction)

    def test_sorted_line_ends_after_one_pass(self):
        g = self.check_line(list(range(32)), "E")
        self.assertEqual(len(g.reads), 32)
        self.assertEqual(g.swaps, 0)
        self.assertEqual(g.moves, 31)

    def test_sorted_ends_are_excluded(self):
        values = list(range(32))
        values[15], values[16] = values[16], values[15]
        g = self.check_line(values, "E")
        self.assertLess(len(g.reads), 64)
        self.assertEqual(g.swaps, 1)

    def test_invalid_line_does_not_wrap_or_mutate(self):
        g = Grid(4)
        for start, size, direction in (((0, 0), 5, "E"), ((0, 0), 2, "W"), ((3, 3), 2, "N"), ((1, 0), 2, "S")):
            self.assertFalse(g.ns["shaker_sort"](start, size, direction))
        self.assertEqual(g.reads, [])
        self.assertEqual(g.moves, 0)

    def test_grid_rows_and_columns_remain_sorted(self):
        for size in (2, 5, 8, 16, 32):
            g = Grid(size)
            rng = random.Random(size)
            g.cells = {p: rng.randrange(10) for p in g.cells}
            original = sorted(g.cells.values())
            g.ns["sort_cactus_grid"]()
            self.assertEqual(sorted(g.cells.values()), original)
            for x in range(size):
                for y in range(size):
                    if x + 1 < size: self.assertLessEqual(g.cells[x, y], g.cells[x+1, y])
                    if y + 1 < size: self.assertLessEqual(g.cells[x, y], g.cells[x, y+1])

    def test_parser_subset(self):
        self.assertEqual(violations(Path("src/cacti_util.py").read_text()), [])


if __name__ == "__main__":
    unittest.main()
