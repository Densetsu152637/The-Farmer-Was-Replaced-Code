import util

# Dictionary acting as a safe, mutable container for persistent state tracking
maze_mem = dict()
maze_mem["visited"] = dict()
maze_mem["path_stack"] = []

# Fixed mapping directions and their absolute backtracking inverses
directions = [North, East, South, West]
opposite_dirs = [South, West, North, East]

def back_direction(direction):
	if direction == North:
		return South
	if direction == East:
		return West
	if direction == South:
		return North
	return East

def clear_maze_memory():
	#Resets tracking keys at the start of a brand new maze sweep.
	global maze_mem
	maze_mem["visited"] = dict()
	maze_mem["path_stack"] = []

def get_current_key():
	#Returns engine-friendly string format mapping for the drone's position.
	return str(get_pos_x()) + "_" + str(get_pos_y())

def get_target_key(d):
	#Predicts the string key of an adjacent tile based on movement vector.
	cx, cy = get_pos_x(), get_pos_y()
	if d == North:
		cy += 1
	elif d == South:
		cy -= 1
	elif d == East:
		cx += 1
	elif d == West:
		cx -= 1
	size = get_world_size()
	return str(cx % size) + "_" + str(cy % size)

def register_visit():
	#Locks current coordinates into memory.
	global maze_mem
	maze_mem["visited"][get_current_key()] = True

def is_visited(target_key):
	#Checks if a target coordinate has already been processed.
	global maze_mem
	return target_key in maze_mem["visited"]

def push_return_path(opposite_dir):
	#Saves the return direction vector.
	global maze_mem
	maze_mem["path_stack"].append(opposite_dir)

def pop_return_path():
	#Extracts the immediate next backtracking step if one exists.
	global maze_mem
	if len(maze_mem["path_stack"]) > 0:
		return maze_mem["path_stack"].pop()
	return None


def maze_branch_worker(first_direction=None, blocked=None):
	# Each drone owns its visited set. Pass ancestor visits explicitly so a
	# child cannot turn back into work already assigned above its fork.
	visited = dict()
	if blocked != None:
		visited = dict(blocked)
	visited[get_current_key()] = True
	path = []
	handles = []
	prefixes = []
	best_route = None
	failed = False
	if first_direction != None:
		if not move(first_direction):
			return None
		path.append(first_direction)
	branch_depth = len(path)

	while True:
		visited[get_current_key()] = True
		if get_entity_type() == Entities.Treasure:
			best_route = list(path)
			break
		choices = []
		for direction in directions:
			target = get_target_key(direction)
			if target not in visited and can_move(direction):
				choices.append((direction, target))

		# Keep one branch for this drone; delegate siblings at the junction.
		for index in range(1, len(choices)):
			direction, target = choices[index]
			child = spawn_drone(maze_branch_worker, direction, visited)
			if child != None:
				handles.append(child)
				prefixes.append(list(path))
				visited[target] = True

		if len(choices) > 0:
			direction, target = choices[0]
			if move(direction):
				path.append(direction)
			else:
				visited[target] = True
			continue

		# The branch is exhausted. Leave the caller's junction untouched.
		if len(path) == branch_depth:
			break
		if not move(back_direction(path.pop())):
			failed = True
			break

	# Never destroy the maze while any descendant is still navigating it.
	for index in range(len(handles)):
		result = wait_for(handles[index])
		if result != None and best_route == None:
			best_route = prefixes[index] + result
	# Every worker returns to its spawn position, even after a local find.
	while len(path) > 0:
		if not move(back_direction(path.pop())):
			failed = True
			break
	if failed:
		return None
	return best_route


def maze_substance_cost():
	level = num_unlocked(Unlocks.Mazes)
	if level < 1:
		return 0
	return get_world_size() * 2 ** (level - 1)


def create_maze():
	amount = maze_substance_cost()
	if amount == 0 or num_items(Items.Weird_Substance) < amount:
		return False
	# Existing mazes must be solved before attempting ordinary navigation.
	if get_entity_type() == Entities.Hedge or get_entity_type() == Entities.Treasure:
		return False
	centre = get_world_size() // 2
	util.go_to(centre, centre)
	util.harvest_if_not(Entities.Bush)
	if get_entity_type() != Entities.Bush:
		if not plant(Entities.Bush):
			return False
	if not use_item(Items.Weird_Substance, amount):
		return False
	return get_entity_type() == Entities.Hedge or get_entity_type() == Entities.Treasure


def solve_maze():
	# Search without harvesting, then follow the winning route after all joins.
	if get_entity_type() != Entities.Hedge and get_entity_type() != Entities.Treasure:
		return False
	route = maze_branch_worker()
	if route == None:
		return False
	for direction in route:
		if not move(direction):
			return False
	if get_entity_type() != Entities.Treasure:
		return False
	before = num_items(Items.Gold)
	harvest()
	return num_items(Items.Gold) > before
