import util

# Dictionary acting as a safe, mutable container for persistent state tracking
maze_mem = dict()
maze_mem["visited"] = dict()
maze_mem["path_stack"] = []

# Fixed mapping directions and their absolute backtracking inverses
directions = [North, East, South, West]
opposite_dirs = [South, West, North, East]

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
	