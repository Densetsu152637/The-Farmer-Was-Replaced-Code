# The Farmer Was Replaced built-ins

This is a practical reference to the game-provided callable built-ins and related predefined values. Signatures and behavior are based on the community wiki's indexed **Available Functions** and **Tooltips** pages, checked 18 September 2026. The game changes over time and unlocks gate some entries, so treat the in-game editor's generated `__builtins__.py` as the final authority for the installed version. The wiki page is currently the best consolidated public inventory; this file should not be treated as an unconditional promise that every historical or experimental function exists in every release.

Source links: [Available Functions](https://thefarmerwasreplaced.wiki.gg/wiki/Available_Functions), [Tooltips](https://thefarmerwasreplaced.wiki.gg/wiki/Tooltips), [Megafarm](https://thefarmerwasreplaced.wiki.gg/wiki/Megafarm), and [External Editor](https://thefarmerwasreplaced.wiki.gg/wiki/External_Editor).

## World, movement, and sensing

| Signature | Returns | Purpose and constraints |
|---|---|---|
| `move(direction)` | `bool` | Move one tile; farm edges wrap. `North`, `South`, `East`, and `West` are directions. Returns `False` when blocked (for example by a maze wall). |
| `can_move(direction)` | `bool` | Check whether `move(direction)` can succeed. |
| `get_pos_x()` | `int` | Current x coordinate; 0 starts at west and increases east. |
| `get_pos_y()` | `int` | Current y coordinate; 0 starts at south and increases north. |
| `get_world_size()` | `int` | Current square farm side length. |
| `set_world_size(size)` | `None` | Set a temporary square size, clear the farm, and reset position. Sizes below 3 restore full size. |
| `get_entity_type()` | entity or `None` | Entity under the drone. |
| `get_ground_type()` | ground | Ground under the drone (`Grounds.Grassland` or `Grounds.Soil`). |
| `measure(direction=None)` | number, position, or `None` | Measure the current or neighboring entity. Meaning is entity-specific: sunflower petals, cactus size, pumpkin value, or next treasure/apple position. |
| `get_companion()` | list or `None` | Companion preference of the plant under the drone; list is `[entity_type, x, y]`. |
| `get_water()` | number | Water level at the tile, from 0 to 1. |

## Farming and inventory

| Signature | Returns | Purpose and constraints |
|---|---|---|
| `harvest()` | `bool` | Harvest/remove the entity under the drone. An unharvestable entity is destroyed; `False` means nothing was removed. |
| `can_harvest()` | `bool` | Whether the entity under the drone is ready. |
| `plant(entity)` | `bool` | Plant an entity if possible; otherwise does nothing and returns `False`. |
| `till()` | `None` | Toggle the current ground between grassland and soil. |
| `swap(direction)` | `bool` or `None` | Swap the current entity with its neighbor. Only some entities support swapping; empty tiles are allowed. |
| `use_item(item, n=1)` | `bool` | Use an item repeatedly where supported, such as `Items.Water`/`Items.Water_Tank` and fertilizer. |
| `num_items(item)` | `int` | Inventory quantity. |
| `get_cost(thing)` | dict or `None` | Cost of buying an item, planting an entity, or unlocking an unlock. Upgradeable unlocks at maximum level may return `None` (older versions returned `{}`). |
| `unlock(unlock)` | `bool` | Perform the corresponding research-tree action. |
| `num_unlocked(thing)` | `int` | 0/1 for ordinary unlock state; for upgrades, 1 plus upgrade count. |

## Timing, output, and control

| Signature | Returns | Purpose and constraints |
|---|---|---|
| `get_tick_count()` | `int` | Operations/ticks since execution began; costs 0 ticks. |
| `get_time()` | number | Game time in seconds since game start. |
| `do_a_flip()` | `None` | Make the drone flip; takes real time and is not speed-up affected. |
| `pet_the_piggy()` | `None` | Pet the piggy; a debug/nostalgia action in the public stub. |
| `print(*values)` | `None` | Show smoke text above the drone; real-time action. |
| `quick_print(*values)` | `None` | Write output without the smoke delay. |
| `set_execution_speed(speed)` | `None` | Set display execution speed; zero/negative restores maximum. |
| `clear()` | `None` | Remove farm entities and reset the drone to `(0, 0)` (and, in some versions, reset its hat). |
| `leaderboard_run(leaderboard, file_name, speedup)` | `None` | Start a named leaderboard simulation at the requested speedup; availability depends on the leaderboard/simulation unlocks. |
| `simulate(filename, sim_unlocks, sim_items, sim_globals, seed, speedup)` | `float` | Run a simulation from supplied unlocks, inventory, globals, seed, and speed; returns elapsed simulated time. Simulation unlock required. |
| `change_hat(hat)` | `None` | Change the drone hat, for example `Hats.Dinosaur_Hat`. |

## Drones

| Signature | Returns | Purpose and constraints |
|---|---|---|
| `spawn_drone(function, *args)` | drone handle or `None` | Spawn at the caller's position and invoke `function(*args)`. Returns `None` at the drone limit; drones have separate memory. |
| `num_drones()` | `int` | Number of active drones. |
| `max_drones()` | `int` | Maximum active drones for the current unlocks. |
| `has_finished(drone)` | `bool` | Check whether a spawned drone ended without waiting. |
| `wait_for(drone)` | called function's return value | Wait for a spawned drone to finish. |

## General language/library built-ins

These are available as the game's Python-like language unlocks permit: `range(end)`, `range(start, end[, step])`, `len(collection)`, `list(collection=None)`, `dict(dictionary=None)`, `set(collection=None)`, `min(*args)`, `max(*args)`, `abs(number)`, `str(object)`, and `random()`. Lists, dictionaries, and sets also expose their supported methods (for example `append`, `insert`, `pop`, `keys`, and `add`); these are object operations, not separate game functions. They follow the signatures and game tick costs described by the wiki/stub; they are not Python imports. `def`, `return`, `if`, `while`, `for`, `continue`, and `not` are language syntax/operators rather than game API functions.

## Predefined values and namespaces

Directions: `North`, `South`, `East`, `West`. Also predefined: `True`, `None`.

The namespaces are iterable collections whose members vary with game updates and unlocks: `Entities`, `Grounds`, `Items`, `Unlocks`, `Hats`, and `Leaderboards`. Common examples include `Entities.Bush`, `Entities.Carrot`, `Grounds.Soil`, `Items.Fertilizer`, and `Unlocks.Carrots`; inspect the installed game's `__builtins__.py` for the exact current member set.

## Removed or version-sensitive names

`get_op_count()` is documented as removed; use `get_tick_count()`. The indexed wiki documents `trade(item, n=1)` and `timed_reset()`, but the public [`__builtins__.py` stub](https://raw.githubusercontent.com/Flekay/The-Farmer-Was-Replaced/main/__builtins__.py) cross-check has no definitions for either, so treat them as historical/version-specific until confirmed in the installed save. Older wiki snapshots use `Items.Water`, while newer content may use `Items.Water_Tank`; use the enum exposed by the installed version. `can_move`, drone functions, sensing, watering, simulation, hats, and crop-specific values are unlock-gated. Function availability and return details can therefore differ between saves and releases.
