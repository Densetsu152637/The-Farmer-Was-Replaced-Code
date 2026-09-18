import globals

MAX_VALUE = 9999999999999999


def update_target_items_for_upgrades():
	# Reset targets for this permutation of farming activity
	for item in globals.ALL_FARMABLE_ITEMS:
		globals.TARGET_ITEMS[item] = globals.MIN_ITEM
	

	while True:
		cheapest_upgrade = None
		cheapest_costs = None
		lowest_total_cost = None

		# Find cheapest active/incomplete upgrade
		for upgrade in globals.UPGRADES_LIST:
			costs = get_cost(upgrade)

			# Completed/maxed upgrades return None or {}
			if costs == None or len(costs) == 0:
				continue

			total_cost = 0
			for item in costs:
				total_cost += costs[item]
				if item not in globals.ALL_FARMABLE_ITEMS:
					total_cost += MAX_VALUE

			if lowest_total_cost == None or total_cost < lowest_total_cost:
				lowest_total_cost = total_cost
				cheapest_upgrade = upgrade
				cheapest_costs = costs

		# No upgrades remain
		if cheapest_upgrade == None:
			return

		# If we already have everything, unlock it and recalculate.
		if can_afford(cheapest_costs):
			unlock(cheapest_upgrade)
			continue

		# This is the next upgrade that requires actual farming.
		for item in cheapest_costs:
			globals.TARGET_ITEMS[item] = cheapest_costs[item]

		return


def can_afford(cost_dict):
	for item in cost_dict:
		if num_items(item) < cost_dict[item]:
			return False

	return True