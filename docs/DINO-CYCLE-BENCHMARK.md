# Dinosaur cycle benchmark ? 32?32

Run date: 2026-09-20. Production scripts were not changed.

## Method

The benchmark executes the actual functions from `src/dino_util.py`, with
host-side overrides for the cycle, shortcut occupancy cutoff, and move ranking.
It preserves the existing tail safety checks, food-overtaking checks and growth
buffer. It models non-wrapping movement and growth on leaving an apple.
Apples are sampled uniformly from free cells. Food costs, movement tick discounts,
interpreter overhead and cycle construction costs are not modeled. These are
movement counts, not measured game completion times.

32?32 is the reported maximum board size; the local save has `expand_8`.
Reference: https://steamcommunity.com/app/2060160/discussions/0/601918052458865348/

Layouts: existing serpentine, randomized growing-tree maze, randomized depth-first
maze, and connected concentric rings. The growing-tree variant chooses a random
frontier vertex then a random unvisited neighbor; it is Prim-like, not a uniform
random-edge Prim implementation. Maze layouts vary with each seed. Every generated
route is checked for complete coverage and closure. All share the same direction
tie-breaking order. Ring orientation and other possible layouts were not exhaustively
searched.

Screening: 8 seeds for each of 20 combinations. All four layouts used cycle-distance
and Manhattan-distance ranking at 50% and 75% occupancy cutoffs; 25% was also tested
with cycle-distance ranking. The 50% cycle-distance configuration won for each layout.
The best two were then tested on 30 new seeds each, without retuning.

The simulator checks boundaries, collisions, queue length, body occupancy and food
progress. Its optimized implementation exactly matched the existing regression
simulator on 10 small-board seeds. Matching seeds use matching random streams,
but different paths produce different free-cell sets and apple coordinates.

## Results

| Layout | Best screening mean moves (8 seeds) | Holdout mean moves (30 seeds) |
|---|---:|---:|
| Serpentine | 132,770 | 132,279 |
| Growing-tree maze | 134,426 | 134,548 |
| Depth-first maze | 137,567 | ? |
| Concentric rings | 172,528 | ? |

All 220 games filled the board without detected collisions or progress loops.
The maze used 1.7% more moves than serpentine in the holdout sample. This supports
retaining the current implementation among these candidates, not a claim that
serpentine is globally optimal. More aggressive shortcuts (75%) and Manhattan
ranking both made these tested configurations slower.

## Reproduce

Run from the repository root:

```powershell
python tests/benchmark_dino_cycles.py
python tests/benchmark_dino_cycles.py --cutoffs 0.25 --rankings cycle --output docs/dino-cycle-early-cutoff.json
python tests/benchmark_dino_cycles.py --layouts baseline prim --cutoffs 0.5 --rankings cycle --start 100 --seeds 30 --output docs/dino-cycle-holdout.json
```

Per-run movement counts and failures are in the three adjacent JSON result files.
