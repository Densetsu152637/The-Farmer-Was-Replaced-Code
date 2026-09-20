# The-Farmer-Was-Replaced-Code
Optimal code for the game

Upgrade selection uses the sum of `max(0, cost - inventory) * weight` for
every required item. Adjust `UPGRADE_ITEM_WEIGHTS` in `src/globals.py` to tune
relative farming effort: hay 1, wood 2, carrots 3, power 4, pumpkins 5,
cactus 6, weird substance 8, treasure/gold 12, and bones 20. These are
heuristic costs, not measured times; setup, input consumption, yields, and
parallelism are approximated by the weights rather than simulated.

Affordable upgrades rank first. Ties use total weighted purchase cost, then
`UPGRADES_LIST` order. Missing resources must be both supported by a farming
policy and unlocked; already-owned resources remain usable. Successful
purchases trigger a fresh comparison. Failed purchases are skipped until
another purchase succeeds or the next planning pass. The API does not expose
research prerequisites through `get_cost`, so an unaffordable candidate can
still have an unmet prerequisite that is only detected when buying it.

Farm targets remain actual inventory amounts with a `MIN_ITEM` floor.
The installed API's `None` cost marks completed research; an empty cost
dictionary is treated as a free purchase, with failed attempts bounded.
