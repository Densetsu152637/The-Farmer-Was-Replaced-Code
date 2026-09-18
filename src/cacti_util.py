import util

def sort_cactus_grid():
	size = get_world_size()
	
	# --- PHASE 1: Zero-Waste Localized Cluster Sorting ---
	# Step through the grid in steps of 4 to handle distinct blocks
	for y_quad in range(0, size, 4):
		for x_quad in range(0, size, 4):
			optimize_2x2_cluster(x_quad, y_quad, size)
			
	# --- PHASE 2: Shaker Sort Every Row ---
	# Uses dynamic bound contraction to instantly clip sorted ends
	for y in range(size):
		shaker_sort_row(y, size)
		
	# --- PHASE 3: Shaker Sort Every Column ---
	# Uses dynamic bound contraction to instantly clip sorted ends
	for x in range(size):
		shaker_sort_column(x, size)
			
	# --- PHASE 4: Global Merge Validation Pass ---
	# The pre-sorted clusters allow the validation pass to clear rapidly
	while gnome_validation_sweep(size):
		continue


def optimize_2x2_cluster(cx, cy, size):
	# Safe boundary lookaheads
	has_east = (cx + 1) < size
	has_north = (cy + 1) < size

	# Execute 2 localized sorting iterations directly over the local loop path
	# This avoids fancy memory sorting arrays that the game parser struggles with
	for pass_num in range(2):
		# Step A: Check and swap Bottom Row horizontally
		if has_east:
			util.go_to(cx, cy)
			left_sz = measure()
			util.go_to(cx + 1, cy)
			right_sz = measure()
			if left_sz > right_sz:
				util.go_to(cx, cy)
				swap(East)

		# Step B: Check and swap Right Column vertically
		if has_east and has_north:
			util.go_to(cx + 1, cy)
			bottom_sz = measure()
			util.go_to(cx + 1, cy + 1)
			top_sz = measure()
			if bottom_sz > top_sz:
				util.go_to(cx + 1, cy)
				swap(North)

		# Step C: Check and swap Top Row horizontally
		if has_east and has_north:
			util.go_to(cx, cy + 1)
			left_sz = measure()
			util.go_to(cx + 1, cy + 1)
			right_sz = measure()
			if left_sz > right_sz:
				util.go_to(cx, cy + 1)
				swap(East)

		# Step D: Check and swap Left Column vertically
		if has_north:
			util.go_to(cx, cy)
			bottom_sz = measure()
			util.go_to(cx, cy + 1)
			top_sz = measure()
			if bottom_sz > top_sz:
				util.go_to(cx, cy)
				swap(North)


def shaker_sort_row(y, size):
	# Row Shaker Sort: Compresses borders to the exact last swapped index
	start = 0
	end = size - 1
	
	while start < end:
		# Track the location of the absolute last swap to trim our boundaries
		last_swap_idx = start
		
		# Forward Pass: Bubble heavy elements up to the right boundary
		for x in range(start, end):
			util.go_to(x, y)
			current_size = measure()
			util.go_to(x + 1, y)
			east_size = measure()
			
			if current_size > east_size:
				util.go_to(x, y)
				swap(East)
				last_swap_idx = x # Mark the position where sorting is still active
				
		# Shrink the right end boundary to where the last swap actually occurred
		end = last_swap_idx
		
		# If the forward pass shrunk or closed the boundaries, we are done
		if start >= end:
			break
			
		last_swap_idx = end
		
		# Backward Pass: Bubble light elements down to the left boundary
		for x in range(end - 1, start - 1, -1):
			util.go_to(x, y)
			current_size = measure()
			util.go_to(x + 1, y)
			east_size = measure()
			
			if current_size > east_size:
				util.go_to(x, y)
				swap(East)
				last_swap_idx = x + 1 # Mark the position where sorting is still active
				
		# Expand the left start boundary to where the last reverse swap occurred
		start = last_swap_idx


def shaker_sort_column(x, size):
	# Column Shaker Sort: Compresses borders to the exact last swapped index
	start = 0
	end = size - 1
	
	while start < end:
		# Track the location of the absolute last swap to trim our boundaries
		last_swap_idx = start
		
		# Forward Pass: Bubble heavy elements up to the top boundary
		for y in range(start, end):
			util.go_to(x, y)
			current_size = measure()
			util.go_to(x, y + 1)
			north_size = measure()
			
			if current_size > north_size:
				util.go_to(x, y)
				swap(North)
				last_swap_idx = y # Mark the position where sorting is still active
				
		# Shrink the upper boundary to where the last swap actually occurred
		end = last_swap_idx
		
		# If the forward pass shrunk or closed the boundaries, we are done
		if start >= end:
			break
			
		last_swap_idx = end
		
		# Backward Pass: Bubble light elements down to the bottom boundary
		for y in range(end - 1, start - 1, -1):
			util.go_to(x, y)
			current_size = measure()
			util.go_to(x, y + 1)
			north_size = measure()
			
			if current_size > north_size:
				util.go_to(x, y)
				swap(North)
				last_swap_idx = y + 1 # Mark the position where sorting is still active
				
		# Expand the lower start boundary to where the last reverse swap occurred
		start = last_swap_idx


def gnome_validation_sweep(size):
	total_cells = size * size
	i = 1
	any_swaps_this_pass = False
	
	while i < total_cells:
		x = i % size
		y = i // size
		
		if i == 0:
			i += 1
			continue
			
		# Skip row wrapping conversions since the elements are not adjacent
		if x == 0:
			i += 1
			continue
			
		prev_x = (i - 1) % size
		prev_y = (i - 1) // size
		
		util.go_to(prev_x, prev_y)
		prev_size = measure()
		util.go_to(x, y)
		curr_size = measure()
		
		if prev_size == None or curr_size == None or prev_size <= curr_size:
			i += 1
		else:
			util.go_to(prev_x, prev_y)
			if x > prev_x:
				swap(East)
			elif y > prev_y:
				swap(North)
			any_swaps_this_pass = True
			i -= 1
			
	return any_swaps_this_pass
