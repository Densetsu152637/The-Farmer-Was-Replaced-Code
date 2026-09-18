import globals


def shortage_of(item):
	return num_items(item) < globals.MIN_ITEM


def lacks_item(item):
	return num_items(item) < globals.TARGET_ITEMS[item] or shortage_of(item)

	
def has_some(item): 
	return num_items(item) > (get_world_size() * get_world_size())
	

def is_even(num):
	return not (num % 2)	
	
	
def harvest_if():
	res = can_harvest()
	if res:		
		harvest()
	return res
	

def harvest_if_not(e):
	res = get_entity_type() != e
	if res:
		harvest()
	return res
	
	
def till_if_required(target):
	while get_ground_type() != target:
		till()
		

def water_if_possible():
	if get_water() < 0.75 and has_some(Items.Water):
		use_item(Items.Water)
		
		
def go_to(target_x, target_y):
	size = get_world_size()
	
	# Move horizontally (X-axis)
	while get_pos_x() != target_x:
		curr_x = get_pos_x()
		# Calculate standard distance vs wrapped distance
		direct_dist = (target_x - curr_x) % size
		wrapped_dist = (curr_x - target_x) % size
		
		if direct_dist < wrapped_dist:
			move(East)
		else:
			move(West)
			
	# Move vertically (Y-axis)
	while get_pos_y() != target_y:
		curr_y = get_pos_y()
		# Calculate standard distance vs wrapped distance
		direct_dist = (target_y - curr_y) % size
		wrapped_dist = (curr_y - target_y) % size
		
		if direct_dist < wrapped_dist:
			move(North)
		else:
			move(South)
			

def go_to_coord(coord):
	go_to(coord[0], coord[1])
	
	
def reposition():
	go_to(0, 0)
	
		
def revert_tile():	
	harvest_if()
	till_if_required(Grounds.Soil)
	
	
def action_per_tile(action):
	reposition()	
	w_l = get_world_size()
	
	# Step 1: Process (0,0) first, then immediately step up to (0,1)
	if action():
		return
	move(North)
	
	# Explicitly perform the action on (0, 1) right after moving here
	if action():
		return
		
	vert = North
	for i in range(w_l):        
		# Loop exactly w_l - 1 times to cover rows 1 through w_l - 1
		for j in range(w_l - 1):
			# Skip the very first tile of the first column since we handled it above
			if not (i == 0 and j == 0):
				if action():
					return 
			
			if j < w_l - 2:
				move(vert)
				
		# Move to the next column if we aren't on the final column boundary
		if i < w_l - 1:
			move(East)
			if vert == North:
				vert = South
			else:
				vert = North
				
	# Step 2: Once it hits x = w_l - 1, drop straight down to the bottom row (y = 0)
	while get_pos_y() > 0:
		move(South)
		
	# Step 3: Sweep step-by-step from right to left across the remaining y = 0 cells
	# Starts at (w_l-1, 0) and finishes right before (0,0) which was already processed
	for x in range(w_l - 1, 0, -1):
		if action():
			return
		move(West)
		
	# Drone naturally ends up back at (0,0) completely finished!
	
	
def reset_farm():
	change_hat(Hats.Straw_Hat)
	action_per_tile(revert_tile)
	

def generate_all_tiles():
	# Generates an ordered list of (x, y) coordinate tuples following the new snake pattern
	tiles_sequence = []
	w_l = get_world_size()
	
	# Step 1: Append the starting point (0, 0)
	tiles_sequence.append((0, 0))
	
	# Step 2: Generate the columns snake pattern, completely ignoring the bottom row (y = 0)
	for i in range(w_l):
		# Even columns snake UP from y = 1 to w_l - 1
		if i % 2 == 0:
			for j in range(1, w_l):
				tiles_sequence.append((i, j))
		# Odd columns snake DOWN from y = w_l - 1 down to 1
		else:
			for j in range(w_l - 1, 0, -1):
				tiles_sequence.append((i, j))
				
	# Step 3: From the far right corner, drop down to the bottom row
	# The snake ends at x = w_l - 1. We step down to y = 0 at that same column.
	# Sweep right-to-left across row 0, ending just before (0, 0)
	for x in range(w_l - 1, 0, -1):
		tiles_sequence.append((x, 0))
				
	return tiles_sequence
	

		