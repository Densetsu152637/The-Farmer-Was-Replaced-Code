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


def maze_disappeared():
	# Bush, grass, and empty tiles all mean another drone ended the maze.
	entity = get_entity_type()
	return entity != Entities.Hedge and entity != Entities.Treasure


def maze_branch_worker(first_direction=None, blocked=None):
	# Copied ancestor visits keep children inside their assigned subtree.
	if maze_disappeared():
		return
	visited = dict()
	if blocked != None:
		visited = dict(blocked)
	visited[get_current_key()] = True
	path = []
	if first_direction != None:
		if maze_disappeared() or not move(first_direction):
			return

	while True:
		entity = get_entity_type()
		if entity != Entities.Hedge and entity != Entities.Treasure:
			return
		if entity == Entities.Treasure:
			harvest()
			return
		visited[get_current_key()] = True
		choices = []
		for direction in directions:
			target = get_target_key(direction)
			if target not in visited and can_move(direction):
				choices.append((direction, target))

		# Keep the first exit. Rejected siblings remain unvisited so normal
		# DFS picks them up when this drone backtracks to the junction.
		for index in range(1, len(choices)):
			if maze_disappeared():
				return
			direction, target = choices[index]
			child = spawn_drone(maze_branch_worker, direction, visited)
			if child != None:
				visited[target] = True

		if maze_disappeared():
			return
		if len(choices) > 0:
			direction, target = choices[0]
			if move(direction):
				path.append(direction)
			else:
				visited[target] = True
			continue

		# Do not join descendants or return to the spawn tile: finishing
		# this subtree immediately releases a drone slot for another fork.
		if len(path) == 0:
			return
		if not move(back_direction(path.pop())):
			return


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
	if maze_disappeared():
		return False
	before = num_items(Items.Gold)
	maze_branch_worker()
	# Only the main drone waits. Descendants may outlive their parents;
	# drain all of them before the policy can create the next maze.
	while num_drones() > 1:
		pass
	return num_items(Items.Gold) > before
