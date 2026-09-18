STATE_NEED_PLANT = 0
STATE_NEED_INFECT = 1
STATE_PERFECT = 2

# Global dictionary tracking mechanism.
infected_cache = dict()

def get_key(x, y):
	#Returns the flattened string key required by the game engine.
	return str(x) + "_" + str(y)

def clear_cache_at_current():
	#Call this immediately whenever you harvest a tile to keep cache accurate.
	global infected_cache
	coord_key = get_key(get_pos_x(), get_pos_y())
	if coord_key in infected_cache:
		infected_cache.pop(coord_key)

def get_weird_substance_requirement():
	global infected_cache
	current_entity = get_entity_type()
	coord_key = get_key(get_pos_x(), get_pos_y())
	
	if current_entity == None:
		if coord_key in infected_cache:
			infected_cache.pop(coord_key)
		return STATE_NEED_PLANT
	
	if current_entity == Entities.Bush:
		if coord_key in infected_cache and infected_cache[coord_key] == True: 
			return STATE_PERFECT
		else:
			return STATE_NEED_INFECT
			
	return STATE_NEED_PLANT

def current_tile_matches(target_state):
	global infected_cache
	current_entity = get_entity_type()
	coord_key = get_key(get_pos_x(), get_pos_y())
	
	is_cached_infected = False
	if coord_key in infected_cache:
		is_cached_infected = infected_cache[coord_key]
	
	if target_state == STATE_NEED_PLANT:
		return current_entity == None
	if target_state == STATE_NEED_INFECT:
		return current_entity == Entities.Bush and not is_cached_infected
	if target_state == STATE_PERFECT:
		return current_entity == Entities.Bush and is_cached_infected
	return False

def plant_dynamic(target_state):
	global infected_cache
	current_entity = get_entity_type()
	x, y = get_pos_x(), get_pos_y()
	coord_key = get_key(x, y)
	
	is_cached_infected = False
	if coord_key in infected_cache:
		is_cached_infected = infected_cache[coord_key]
	
	# Pass 1: Plant if bare
	if target_state == STATE_NEED_PLANT or current_entity == None:
		if coord_key in infected_cache:
			infected_cache.pop(coord_key)
		plant(Entities.Bush)
		current_entity = Entities.Bush 
		
	# Pass 2: Infect using optimization mechanics
	if target_state == STATE_NEED_INFECT or not is_cached_infected:
		if current_entity == Entities.Bush:
			# OPTIMIZATION: If we have Weird Substance available, use it instead of precious Fertilizer!
			if num_items(Items.Weird_Substance) > 0:
				use_item(Items.Weird_Substance)
				
				# CRITICAL FIX: Weird Substance toggles the current plant AND all 4 neighbors.
				# We must mirror this cross-mutation logic inside our memory grid!
				coords_to_toggle = [(x, y), (x+1, y), (x-1, y), (x, y+1), (x, y-1)]
				for cx, cy in coords_to_toggle:
					k = get_key(cx, cy)
					# Toggle the boolean state in cache
					if k in infected_cache:
						infected_cache[k] = not infected_cache[k]
					else:
						infected_cache[k] = True
			else:
				# Fallback to Fertilizer if we are completely out of Weird Substance
				use_item(Items.Fertilizer)
				infected_cache[coord_key] = True
				