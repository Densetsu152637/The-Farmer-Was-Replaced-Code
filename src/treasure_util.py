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
	return str(cx) + "_" + str(cy)

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


def maze_branch_worker(first_direction):
	visited = dict()
	path = []
	child_handles = []
	child_prefixes = []
	best_route = None
	directions_local = [North, East, South, West]
	backs = [South, West, North, East]
	visited[str(get_pos_x()) + "," + str(get_pos_y())] = True
	if not move(first_direction):
		return None
	path.append(first_direction)
	while True:
		key = str(get_pos_x()) + "," + str(get_pos_y())
		visited[key] = True
		if get_entity_type() == Entities.Treasure:
			best_route = []
			for direction in path:
				best_route.append(direction)
			break
		moved = False
		choices = []
		for i in range(4):
			d = directions_local[i]
			tx, ty = get_pos_x(), get_pos_y()
			if d == North:
				ty += 1
			elif d == South:
				ty -= 1
			elif d == East:
				tx += 1
			else:
				tx -= 1
			target = str(tx) + "," + str(ty)
			if can_move(d) and not (target in visited):
				choices.append((d, target))
		if len(choices) > 1:
			delegated = []
			for d, target in choices[1:]:
				child = spawn_drone(maze_branch_worker, d)
				if child != None:
					child_handles.append(child)
					child_prefixes.append(list(path))
					visited[target] = True
				else:
					delegated.append((d, target))
			choices = choices[:1] + delegated
		if len(choices) > 0:
			d, target = choices[0]
			move(d)
			path.append(d)
			moved = True
		if not moved:
			if len(path) == 1:
				last_direction = path.pop()
				move(back_direction(last_direction))
				break
			last_direction = path.pop()
			move(back_direction(last_direction))
	for i in range(len(child_handles)):
		result = wait_for(child_handles[i])
		if result != None and best_route == None:
			best_route = child_prefixes[i] + result
	if best_route == None:
		return None
	for i in range(len(path) - 1, -1, -1):
		move(back_direction(path[i]))
	return best_route
