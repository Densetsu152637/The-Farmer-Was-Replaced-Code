# Parallel policy models

The entrypoint in `src/main.py` selects one resource policy at a time. Each policy owns disjoint tile work or an explicit phase barrier; `spawn_drone()` returns `None` at capacity and every policy has an inline fallback where it submits work.

| Policy | Worker model | Barrier/failure rule |
|---|---|---|
| Power/sunflowers | Explicit `util.region_bounds(max_drones())` square-block planting; measurement workers return every flower record | Parent merges all records and harvests in petal order. |
| Hay | Explicit disjoint square blocks through `run_parallel_regions` | Join before next round. |
| Wood | Explicit disjoint square blocks through `run_parallel_regions` | Join before next round. |
| Carrots | Explicit disjoint square blocks through `run_parallel_regions` | Join before next round. |
| Pumpkins | Disjoint square-block planting and readiness/repair ownership | All worker results join before a single giant harvest; failed planting aborts. |
| Cactus | Parallel planting, then row-sort barrier, then column-sort barrier | No worker overlaps a row/column phase. |
| Weird Substance | Explicit disjoint grass production bands | Fertilizer-only workers join; no maze/bush/cache/color mutation. |
| Treasure | One fresh full-field maze; workers dynamically delegate extra DFS exits at encountered junctions | Workers return routes and backtrack without harvesting; parent joins all and harvests once. |
| Dinosaur | Parallel farm reset/preparation; one parent dinosaur state machine | The Dinosaurs documentation states only one drone may wear the Dinosaur Hat, so one parent snake is an engine constraint; preparation remains parallel. |

`util.run_parallel_regions()` partitions equal square blocks when the world size
supports them, spawns `_run_region`, executes rejected jobs inline, waits for
every accepted handle, and repositions. The helper chooses the largest square
factor not exceeding the requested worker budget; a non-square or non-divisible
budget therefore intentionally leaves some drone capacity unused rather than
creating uneven edge blocks. Region actions must not mutate neighboring tiles or
rely on shared Python globals because the game copies drone memory.

For other jobs, `util.parallel_map(function, args_list)` owns the same
submission and join boilerplate. Each `args_list` entry is passed as one payload
(tuples/lists can carry several values and a small worker adapter can index them);
the returned list preserves job order, including `None` and `False`. A capacity
rejection executes inline, while every accepted handle is joined before return. Policies still choose their own regions,
rows, columns, or maze branches; dynamic treasure DFS remains bespoke because
each junction decides its next jobs from live maze state.

The game documentation confirms copied worker arguments/no shared memory, `None` on drone capacity, and shared-tile race conditions. Fresh mazes are acyclic; treasure workers therefore branch-search and never mutate the maze. Reusing a maze creates loops and is outside this policy model.

The test harness in `tests/` mocks movement, inventory, worker handles, and joins. It validates ownership and phase ordering; live game growth timing, inventory contention, and maze geometry still require in-game verification.

## Farming strategy notes

Community reports recommend harvesting sunflowers from highest petal count
downward and stopping once the Power target is met; the power policy follows
that ordering and now exits the harvest heap as soon as its target is satisfied.
See [the sunflower discussion](https://www.reddit.com/r/TheFarmerWasReplaced/comments/1ohf9uq/all_my_solutions_except_snake_at_4x_speed/).

Forum pumpkin strategies commonly track only failed coordinates between growth
passes. This implementation uses that sparse pending-coordinate approach while
preserving the parallel ownership and single global harvest barrier.
See [the pumpkin optimization discussion](https://www.reddit.com/r/TheFarmerWasReplaced/comments/1tru4ys/how_can_i_make_my_pumpkin_farm_more_efficient/).

The implementation scans each owned region once, then revisits only the
returned pending coordinates. If a field has `N` tiles and later rounds contain
`k1, k2, ...` pending tiles, movement checks are bounded by `N + k1 + k2 + ...`
instead of rescanning `N` tiles every round. A mature harvestable pumpkin is
removed from the pending set; dead, empty, wrong, or still-growing tiles remain.
