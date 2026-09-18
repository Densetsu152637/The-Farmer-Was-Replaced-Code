import ast
from pathlib import Path
import unittest


def load_traversal():
    # Isolate coordinate generation from unrelated game-only imports.
    tree = ast.parse(Path("src/util.py").read_text())
    function = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef)
                    and node.name == "generate_all_tiles")
    namespace = {"get_world_size": lambda: 6}
    exec(compile(ast.Module(body=[function], type_ignores=[]),
                 "src/util.py", "exec"), namespace)
    return namespace["generate_all_tiles"]


class TileTraversalTests(unittest.TestCase):
    def setUp(self):
        self.generate = load_traversal()

    def test_rectangles_cover_tiles_once_with_adjacent_steps(self):
        for start in ((0, 0), (3, 5)):
            for width in range(1, 9):
                for height in range(1, 9):
                    with self.subTest(start=start, size=(width, height)):
                        path = self.generate(start=start, size=(width, height))
                        expected = {(start[0] + x, start[1] + y)
                                    for x in range(width) for y in range(height)}
                        self.assertEqual(len(path), width * height)
                        self.assertEqual(set(path), expected)
                        self.assertEqual(path[0], start)
                        for first, second in zip(path, path[1:]):
                            self.assertEqual(abs(first[0] - second[0]) +
                                             abs(first[1] - second[1]), 1)
                        if width > 1 and height > 1 and (width % 2 == 0 or height % 2 == 0):
                            self.assertEqual(abs(path[-1][0] - start[0]) +
                                             abs(path[-1][1] - start[1]), 1)

    def test_even_square_order_is_preserved(self):
        for length in (2, 4, 6, 8):
            expected = [(0, 0)]
            for x in range(length):
                rows = range(1, length) if x % 2 == 0 else range(length - 1, 0, -1)
                expected.extend((x, y) for y in rows)
            expected.extend((x, 0) for x in range(length - 1, 0, -1))
            self.assertEqual(self.generate(length=length), expected)

    def test_defaults_and_square_calls(self):
        self.assertEqual(self.generate(), self.generate(size=(6, 6)))
        for length in range(1, 9):
            self.assertEqual(self.generate((2, 3), length),
                             self.generate((2, 3), size=(length, length)))

    def test_return_lane_orientation(self):
        self.assertEqual(self.generate(size=(4, 3))[-3:], [(3, 0), (2, 0), (1, 0)])
        self.assertEqual(self.generate(size=(3, 4))[-3:], [(0, 3), (0, 2), (0, 1)])
        self.assertEqual(self.generate(size=(3, 3))[-1], (2, 2))

    def test_empty_blocks(self):
        for size in ((0, 3), (3, 0), (-1, 3), (3, -1)):
            self.assertEqual(self.generate(size=size), [])


if __name__ == "__main__":
    unittest.main()
