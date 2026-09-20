import globals


def integer_sqrt(n: int) -> int:
    # assume n >= 0    
    # Base cases for 0 and 1
    if n < 2:
        return n
        
    low = 1
    high = n // 2
    ans = 0
    
    while low <= high:
        mid = (low + high) // 2
        mid_squared = mid * mid
        
        if mid_squared == n:
            return mid
        elif mid_squared < n:
            ans = mid  # mid could be the floor square root
            low = mid + 1
        else:
            high = mid - 1
            
    return ans


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
  
  
def revert_tile():
	harvest_if()
	till_if_required(Grounds.Soil)
 

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

TILE_CACHE = {
	"start": (-1, -1),
 	"size": (-1, -1),
	"sequence": [] 
}

def action_per_tile(action, start=None, size=None):
	global TILE_CACHE
	if TILE_CACHE["start"] != start or TILE_CACHE["size"] != size:
		TILE_CACHE["sequence"] = generate_tile_sequence(start, size)
	go_to_coord(start)
	for tile in TILE_CACHE["sequence"]:
		go_to_coord(tile)
		if action():
			return

def action_per_region(action, region):
    return action_per_tile(action, region["start"], region["size"])


def generate_tile_sequence(start=None, size=None):
    # does not assume grid is even
	if start == None:
		start = (0, 0)

	if size == None:
		size = (get_world_size() - start[0], get_world_size() - start[1])  
  
	# just a straight line
	if size[0] == 1 or size[1] == 1:
		return generate_tile_straight(start, size)
 
	# at least one size even (we can sweep back on this side)
	if not size[0] % 2 or not size[1] % 2:
		return generate_tile_even(start, size)
 
 	# both sides, odd, we cannot use a serpentine pattern so instead we use the closest thing
	return generate_tile_odd(start, size)	


def generate_tile_straight(start, size):
    # Generates an ordered list of (x, y) coordinate tuples going straight
	tiles_sequence = []
    
    # going east
	if size[0] == 1:
		for y in range(size[1]):
			tiles_sequence.append(start[0], start[1] + y)
            
    # going north
	if size[1] == 1:
		for x in range(size[1]):
			tiles_sequence.append(start[0] + x, start[1])        
        
	return tiles_sequence   


def generate_tile_even(start, size):
    # Generates an ordered list of (x, y) coordinate tuples following the new snake pattern
	tiles_sequence = []

	# Step 1: Append the starting point 
	tiles_sequence.append((start[0], start[1]))

	# Step 2: Generate the columns snake pattern, completely ignoring the bottom row (y = 0)
	if not size[0] % 2:
		for x in range(size[0]):
			# Even columns snake forwards from y = 1 to w_l - 1
			if x % 2 == 0:
				for y in range(1, size[1]):
					tiles_sequence.append((start[0] + x, start[1] + y))
			# Odd columns snake backwards from y = w_l - 1 down to 1
			else:
				for y in range(size[1] - 1, 0, -1):
					tiles_sequence.append((start[0] + x, start[1] + y))

		# Step 3: From the bottom right corner, drop down to the bottom left corner
		# Sweep right-to-left across row start[1], ending just before start
		for x in range(size[0] - 1, 0, -1):
			tiles_sequence.append((start[0] + x, start[1]))

	elif not size[1] % 2:
		for y in range(size[1]):
			# Even rows snake forwards from y = 1 to w_l - 1
			if y % 2 == 0:
				for x in range(1, size[0]):
					tiles_sequence.append((start[0] + x, start[1] + y))
			# Odd rows snake backwards from y = w_l - 1 down to 1
			else:
				for x in range(size[0] - 1, 0, -1):
					tiles_sequence.append((start[0] + x, start[1] + y))
     
		# Step 3: From the top left corner, drop down to the bottom row
		# Sweep top-to-bottom across column start[0], ending just before start
		for y in range(size[1] - 1, 0, -1):
			tiles_sequence.append((start[0], start[1] + y))

	return tiles_sequence


def generate_tile_odd(start, size):
    # Generates an ordered list of (x, y) coordinate tuples 
	tiles_sequence = []
	
	# guaranteed to end up in the top right corner anyways
	for x in range(size[0]):
		# Even columns snake forwards from y = start[1] to start[1] + size[1]
		if x % 2 == 0:
			for y in range(size[1]):
				tiles_sequence.append((start[0] + x, start[1] + y))
		# Odd columns snake backwards from y = start[1] + size[1] down to start[1]
		else:
			for y in range(size[1] - 1, -1, -1):
				tiles_sequence.append((start[0] + x, start[1] + y))
    
	return tiles_sequence


def generate_regions(n):
	# Use a square grid whose side is the integer square root of the budget.
	# Remainders are distributed over the first segments on each axis.
	if n < 1:
		n = 1
	size = get_world_size()
	if n > size * size:
		n = size * size
	divisions = integer_sqrt(n)
	if divisions < 1:
		divisions = 1
	base = size // divisions
	remainder = size % divisions
	widths = []
	for index in range(divisions):
		width = base
		if index < remainder:
			width += 1
		widths.append(width)
	heights = []
	for index in range(divisions):
		heights.append(widths[index])
	regions = []
	x0 = 0
	for x_index in range(divisions):
		x1 = x0 + widths[x_index]
		y0 = 0
		for y_index in range(divisions):
			y1 = y0 + heights[y_index]
			regions.append({"start": (x0, y0), "size": (x1 - x0, y1 - y0)})
			y0 = y1
		x0 = x1
	return regions


def parallel_map(function, args_list):
	# Split jobs into balanced contiguous blocks, including one for this drone.
	job_count = len(args_list)
	if job_count == 0:
		return []
	worker_count = min(job_count, max(1, max_drones() - num_drones() + 1))
	block_size = job_count // worker_count
	remainder = job_count % worker_count
	results = []
	for index in range(job_count):
		results.append(None)

	def execute_task(bounds):
		# Drone memory is copied: return this block instead of mutating results.
		batch_results = []
		for index in range(bounds[0], bounds[1]):
			batch_results.append(function(args_list[index]))
		return batch_results

	handles = []
	local_blocks = []
	start = 0
	for block in range(worker_count):
		end = start + block_size
		if block < remainder:
			end += 1
		bounds = (start, end)
		if block == worker_count - 1:
			local_blocks.append(bounds)
		else:
			handle = spawn_drone(execute_task, bounds)
			if handle == None:
				local_blocks.append(bounds)
			else:
				handles.append((start, handle))
		start = end

	# Launch all workers before doing local work, including rejected spawns.
	for bounds in local_blocks:
		batch_results = execute_task(bounds)
		for offset in range(len(batch_results)):
			results[bounds[0] + offset] = batch_results[offset]

	# Join every worker and preserve input order, including None/False results.
	for start, handle in handles:
		batch_results = wait_for(handle)
		for offset in range(len(batch_results)):
			results[start + offset] = batch_results[offset]
	return results



def run_parallel_regions(action, regions=None):
	# Spawn up to the available capacity, and execute failed submissions inline.
	# Joining every handle makes the caller's next phase deterministic.
	# Assumes the action takes in a region as an argument
	if regions == None:
		regions = generate_regions(max_drones())  
	go_to(0, 0)
	return parallel_map(action, regions)

    
def reset_farm(): 
    change_hat(Hats.Straw_Hat)
    def reset_region(region):
        action_per_tile(revert_tile, region["start"], region["size"])        
    
    return run_parallel_regions(reset_region)
