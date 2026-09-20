import globals


def upgrade_score(costs):
	# Remaining farming effort first; total weighted spend breaks ties.
	remaining = 0
	total = 0
	for item in costs:
		weight = 1
		if item in globals.UPGRADE_ITEM_WEIGHTS:
			weight = globals.UPGRADE_ITEM_WEIGHTS[item]
		total += costs[item] * weight
		missing = max(0, costs[item] - num_items(item))
		if missing > 0:
			if item not in globals.ALL_FARMABLE_ITEMS or num_unlocked(item) == 0:
				return None
			remaining += missing * weight
	return [remaining, total]


def get_next_cheapest_upgrade(excluded=None):
	# Return [upgrade, actual costs], or None when no feasible candidate remains.
	best = None
	best_score = None
	for upgrade in globals.UPGRADES_LIST:
		if excluded != None and upgrade in excluded:
			continue
		costs = get_cost(upgrade)
		# Installed API uses None for completed upgrades; {} is a free unlock.
		if costs == None:
			continue
		score = upgrade_score(costs)
		if score == None:
			continue
		if best_score == None or score[0] < best_score[0] or (score[0] == best_score[0] and score[1] < best_score[1]):
			best = [upgrade, costs]
			best_score = score
	return best


def update_target_items_for_upgrades():
	# Targets are inventory totals, never weighted values or missing quantities.
	globals.TARGET_ITEMS = {}
	for item in globals.ALL_FARMABLE_ITEMS:
		globals.TARGET_ITEMS[item] = globals.MIN_ITEM

	failed = []
	while True:
		candidate = get_next_cheapest_upgrade(failed)
		if candidate == None:
			return
		upgrade = candidate[0]
		costs = candidate[1]
		if can_afford(costs):
			if unlock(upgrade):
				# A purchase can satisfy another upgrade's research prerequisite.
				failed = []
			else:
				# Missing prerequisites must not cause an infinite retry.
				failed.append(upgrade)
			continue

		for item in costs:
			if item in globals.ALL_FARMABLE_ITEMS:
				globals.TARGET_ITEMS[item] = max(globals.MIN_ITEM, costs[item])
		return


def can_afford(cost_dict):
	for item in cost_dict:
		if num_items(item) < cost_dict[item]:
			return False
	return True
