import util

def sort_cactus_grid():
	size = get_world_size()
	
	# --- PHASE 2: Shaker Sort Every Row ---
	# Uses dynamic bound contraction to instantly clip sorted ends
	row_jobs = []
	for y in range(size):
		row_jobs.append((y, size))
	util.parallel_map(_sort_row_job, row_jobs)
		
	# --- PHASE 3: Shaker Sort Every Column ---
	# Uses dynamic bound contraction to instantly clip sorted ends
	column_jobs = []
	for x in range(size):
		column_jobs.append((x, size))
	util.parallel_map(_sort_column_job, column_jobs)
			
	# Row and column sorting are complete global barriers: each row and then
	# each column is monotone, so a row-major gnome pass would only undo the
	# column ordering and is intentionally omitted.


def sort_one_row(y, size):
	# Rows are disjoint ownership units; the column phase starts only after
	# every row worker has joined.
	shaker_sort_row(y, size)


def _sort_row_job(job):
	sort_one_row(job[0], job[1])


def sort_one_column(x, size):
	shaker_sort_column(x, size)


def _sort_column_job(job):
	sort_one_column(job[0], job[1])


def shaker_sort_row(y, size):
	for end in range(size - 1, 0, -1):
		for x in range(end):
			util.go_to(x, y)
			left = measure()
			util.go_to(x + 1, y)
			right = measure()
			if left > right:
				util.go_to(x, y)
				swap(East)
	return

def _legacy_shaker_sort_row(y, size):
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
	for end in range(size - 1, 0, -1):
		for y in range(end):
			util.go_to(x, y)
			bottom = measure()
			util.go_to(x, y + 1)
			top = measure()
			if bottom > top:
				util.go_to(x, y)
				swap(North)
	return

def _legacy_shaker_sort_column(x, size):
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
