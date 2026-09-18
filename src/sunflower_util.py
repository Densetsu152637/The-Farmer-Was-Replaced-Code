import heap
known_petals = heap.create_heap()

def get_petal_size(e):
	return e[0]

def add_to_collection():
	global known_petals
	value = [measure(), [get_pos_x(), get_pos_y()]]
	heap.heap_push(known_petals, value, get_petal_size)
	
def get_end():
	global known_petals
	return heap.heap_pop(known_petals)