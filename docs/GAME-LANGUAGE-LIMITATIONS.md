# Game language limitations

This applies to scripts copied into The Farmer Was Replaced and executed by the
game parser, currently the Python files under `src/`. Host-side tests under
`tests/` run in CPython and are outside this restriction.

## Required restrictions

Game scripts must not use:

- conditional expressions (`a if condition else b`);
- inline suites such as `if condition: action()` or one-line `else`/`elif` bodies;
- docstrings (`"""..."""` or `'''...'''`);
- class definitions.

Use ordinary multi-line `if`/`else` blocks, named helper functions, and module
level state where the game API requires it. Keep worker arguments explicit and
return data to the parent because spawned drones have copied memory.

The repository scan found no violations of these four restrictions in `src/`.
Comments containing words such as `if` or `else` are harmless. The project also
keeps a conservative compatibility subset in runtime scripts: no lambdas, list
comprehensions, or starred calls. These extra rules are project style choices,
not claims that every game version rejects those constructs. This document
does not ban other Python features without evidence from the installed game parser;
check [BUILT-IN-FUNCTIONS.md](BUILT-IN-FUNCTIONS.md) and the installed
`__builtins__.py` before relying on version-sensitive syntax or APIs.

The runtime subset also avoids the confirmed unsupported conveniences
`list.index(...)`, `any(...)`, and generator expressions. Replace `index` with
an explicit direction or position mapping, and replace `any` or generators
with a flag updated by an ordinary loop. No `any(...)` call existed in the
current runtime; `list.index(...)` was removed from the maze worker.

The scanner is intentionally separate from the host test suite: tests may use
classes and ordinary Python conveniences, but those files are never copied to
the game.
