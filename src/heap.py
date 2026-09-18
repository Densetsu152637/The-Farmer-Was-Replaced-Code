def create_heap():
	return {"data": [], "size": 0}

def heapify(items, key_func=None):
	# Build a new max heap in linear time without modifying items.
	hp = create_heap()
	data = hp["data"]
	for item in items:
		if key_func != None:
			sort_key = key_func(item)
		else:
			sort_key = item
		data.append((sort_key, item))
	hp["size"] = len(data)
	# Leaves are already heaps; repair parents from the bottom up.
	for idx in range(hp["size"] // 2 - 1, -1, -1):
		sift_down(hp, idx)
	return hp

def heap_merge(heaps):
	# Copy cached (key, item) entries and rebuild once in linear time.
	# Source heaps are unchanged and must use compatible sort keys.
	hp = create_heap()
	data = hp["data"]
	for source in heaps:
		for entry in source["data"]:
			data.append(entry)
	hp["size"] = len(data)
	for idx in range(hp["size"] // 2 - 1, -1, -1):
		sift_down(hp, idx)
	return hp

def heap_push(hp, item, key_func=None):
	data = hp["data"]
	
	if key_func != None: 
		sort_key = key_func(item) 
	else:
		sort_key = item
	
	data.append((sort_key, item))
	hp["size"] += 1
	
	sift_up(hp, hp["size"] - 1)

def heap_peek(hp):
	# Return the largest item without removing it.
	if hp["size"] == 0:
		return None
	return hp["data"][0][1]

def heap_pop(hp):
	data = hp["data"]
	size = hp["size"]
	
	if size == 0:
		return None
	
	root_tuple = data[0]
	root_item = root_tuple[1]
	
	last_tuple = data.pop()
	hp["size"] -= 1
	
	if hp["size"] > 0:
		data[0] = last_tuple
		sift_down(hp, 0)
		
	return root_item

def sift_up(hp, idx):
	data = hp["data"]
	while idx > 0:
		parent_idx = (idx - 1) // 2
		
		# MAX HEAP CHANGE: Swap if the child's key is GREATER than the parent's key
		if data[idx][0] > data[parent_idx][0]:
			temp = data[idx]
			data[idx] = data[parent_idx]
			data[parent_idx] = temp
			idx = parent_idx
		else:
			break

def sift_down(hp, idx):
	data = hp["data"]
	size = hp["size"]
	
	while True:
		left_child = 2 * idx + 1
		right_child = 2 * idx + 2
		largest = idx # Variable renamed to reflect Max-Heap logic
		
		# MAX HEAP CHANGE: Look for the largest key among parent and children
		if left_child < size:
			if data[left_child][0] > data[largest][0]:
				largest = left_child
				
		if right_child < size:
			if data[right_child][0] > data[largest][0]:
				largest = right_child
				
		if largest != idx:
			temp = data[idx]
			data[idx] = data[largest]
			data[largest] = temp
			idx = largest
		else:
			break
