import util

def sort_cactus_grid():
	size = get_world_size()
	
	# --- PHASE 1: Shaker Sort Every Row ---
	# Uses dynamic bound contraction to instantly clip sorted ends
	row_jobs = []
	for y in range(size):
		row_jobs.append((y, size))
	util.parallel_map(_sort_row_job, row_jobs)
		
	# --- PHASE 2: Shaker Sort Every Column ---
	# Uses dynamic bound contraction to instantly clip sorted ends
	column_jobs = []
	for x in range(size):
		column_jobs.append((x, size))
	util.parallel_map(_sort_column_job, column_jobs)
 
def _sort_row_job(job):
	sort_one_row(job[0], job[1])
 
def _sort_column_job(job):
	sort_one_column(job[0], job[1])

def sort_one_row(y, size):
	shaker_sort_row(y, size)

def sort_one_column(x, size):
	shaker_sort_column(x, size)

def shaker_sort_row(y, size):
	return shaker_sort((0, y), size, East)


def shaker_sort_column(x, size):
	return shaker_sort((x, 0), size, North)


def shaker_sort(start, size, direction):
	# Sort a contiguous line, keeping cactus values increasing east/north.
	# West/south starts at the high-coordinate end of the same line.
	if size <= 0:
		return True
	if direction == East:
		dx, dy = 1, 0
		reverse = West
	elif direction == West:
		dx, dy = -1, 0
		reverse = East
	elif direction == North:
		dx, dy = 0, 1
		reverse = South
	elif direction == South:
		dx, dy = 0, -1
		reverse = North
	else:
		return False

	# Do not compare or swap across the farm's wrapping boundary.
	world_size = get_world_size()
	end_x = start[0] + dx * (size - 1)
	end_y = start[1] + dy * (size - 1)
	if min(start[0], end_x) < 0 or max(start[0], end_x) >= world_size:
		return False
	if min(start[1], end_y) < 0 or max(start[1], end_y) >= world_size:
		return False
	if size == 1:
		return True

	util.go_to(start[0], start[1])
	left = 0
	right = size - 1
	index = 0
	step = 1
	travel = direction
	back = reverse
	while left < right:
		end = right
		if step < 0:
			end = left
		last_swap = -1
		current = measure()
		while index != end:
			neighbor = measure(travel)
			out_of_order = current > neighbor
			if travel == West or travel == South:
				out_of_order = current < neighbor
			if out_of_order:
				swap(travel)
				last_swap = index
			else:
				current = neighbor
			# After swapping, current travels with us to the next tile.
			move(travel)
			index += step

		if last_swap == -1:
			return True
		# Everything beyond the last swapped pair is a sorted contiguous
		# suffix/prefix. Exclude it from all remaining comparisons.
		if step > 0:
			right = last_swap
		else:
			left = last_swap
		if left >= right:
			return True
		while index != last_swap:
			move(back)
			index -= step
		step = -step
		temp = travel
		travel = back
		back = temp
	return True
