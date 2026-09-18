# 1. The Initializer Function
def create_circular_queue(initial_capacity):
	queue_list = []
	for i in range(initial_capacity):
		queue_list.append(0) # Using 0 instead of None
		
	return {
		"capacity": initial_capacity,
		"queue": queue_list,
		"head": 0,
		"tail": 0,
		"size": 0
	}

# Helper Function: Safely doubles the internal array and realigns the pointers
def resize_queue(q):
	old_capacity = q["capacity"]
	new_capacity = old_capacity * 2
	
	new_list = []
	for i in range(new_capacity):
		new_list.append(0)
		
	# Extract elements in chronological order (from head to tail)
	for i in range(q["size"]):
		old_index = (q["head"] + i) % old_capacity
		new_list[i] = q["queue"][old_index]
		
	# Reset internal dictionary properties to match the new list layout
	q["queue"] = new_list
	q["capacity"] = new_capacity
	q["head"] = 0
	q["tail"] = q["size"]

# 2. Enqueue Function (Handles dynamic growth automatically)
def enqueue(q, item):
	if q["size"] == q["capacity"]:
		resize_queue(q) # Trigger automatic growth when full
		
	q["queue"][q["tail"]] = item
	q["tail"] = (q["tail"] + 1) % q["capacity"]
	q["size"] += 1
	return True

# 3. Dequeue Function 
def dequeue(q):
	if q["size"] == 0:
		return 0 # Returns 0 instead of None when empty
		
	item = q["queue"][q["head"]]
	q["queue"][q["head"]] = 0 # Clear reference with 0
	q["head"] = (q["head"] + 1) % q["capacity"]
	q["size"] -= 1
	return item