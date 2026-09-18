import ast
import io
import tokenize
from pathlib import Path
import unittest


def violations(source, filename="<source>"):
	result = []
	tree = ast.parse(source, filename=filename)
	for node in ast.walk(tree):
		if isinstance(node, (ast.ClassDef, ast.IfExp, ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
			result.append((filename, type(node).__name__, node.lineno))
		if isinstance(node, ast.Call) and any(isinstance(arg, ast.Starred) for arg in node.args):
			result.append((filename, "starred_call", node.lineno))
		if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "any":
			result.append((filename, "any_call", node.lineno))
		if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "index":
			result.append((filename, "index_call", node.lineno))
		if isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant) and isinstance(node.value.value, str):
			result.append((filename, "docstring", node.lineno))
		if isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.FunctionDef)):
			for child in getattr(node, "body", []):
				if child.lineno == node.lineno:
					result.append((filename, "inline_suite", node.lineno))
	# Catch one-line else/elif suites whose body is on the else/elif line.
	tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
	keywords = {"if", "elif", "else", "for", "while", "def"}
	for i, token in enumerate(tokens[:-1]):
		if token.type == tokenize.NAME and token.string in keywords:
			j = i + 1
			while j < len(tokens) and tokens[j].type not in (tokenize.NEWLINE, tokenize.ENDMARKER):
				if tokens[j].string == ":":
					k = j + 1
					while tokens[k].type in (tokenize.INDENT, tokenize.DEDENT, tokenize.NL, tokenize.COMMENT):
						k += 1
					if tokens[k].type != tokenize.NEWLINE and tokens[k].string not in ("]", ")", "}", ",") and tokens[k].start[0] == token.start[0]:
						result.append((filename, "inline_suite", token.start[0]))
					break
				j += 1
	return result


def runtime_violations():
	result = []
	for path in Path("src").glob("*.py"):
		result.extend(violations(path.read_text(), str(path)))
	return result


class GameLanguageTests(unittest.TestCase):
    def test_runtime_scripts_use_conservative_parser_subset(self):
        self.assertEqual(runtime_violations(), [])

    def test_checker_catches_inline_branches_and_allows_multiline(self):
        for source in ("if flag: work()", "if flag:\n    work()\nelse: other()", "if flag:\n    work()\nelif other: more()"):
            self.assertTrue(violations(source))
        for source in ("if flag:\n    work()\nelse:\n    other()", "text = 'if x: y()'\n# else: z()"):
            self.assertEqual(violations(source), [])

    def test_checker_catches_confirmed_unsupported_calls(self):
        self.assertTrue(violations("directions.index(path.pop())"))
        self.assertTrue(violations("any(value for value in values)"))
        self.assertEqual(violations("found = False\nfor value in values:\n    if value:\n        found = True"), [])

    def test_direction_mapping_covers_all_four_moves(self):
        import sys
        import builtins
        sys.path.insert(0, "src")
        builtins.North, builtins.East = "N", "E"
        builtins.South, builtins.West = "S", "W"
        import treasure_util
        treasure_util.North, treasure_util.East = "N", "E"
        treasure_util.South, treasure_util.West = "S", "W"
        self.assertEqual(treasure_util.back_direction("N"), "S")
        self.assertEqual(treasure_util.back_direction("E"), "W")
        self.assertEqual(treasure_util.back_direction("S"), "N")
        self.assertEqual(treasure_util.back_direction("W"), "E")


if __name__ == "__main__":
	unittest.main()
