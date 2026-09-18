import queue


STATE = {
	"apple_x": -1,
	"apple_y": -1,
	"length": 0,
	"active": False,
	"size": 0,
	"capacity": 0,
	"steps_without_apple": 0
}

BODY = []
HAMILTONIAN = []
HAM_INDEX = []

TAIL = queue.create_circular_queue(1)


def create_matrix(size, value):
	matrix = []

	for x in range(size):
		column = []

		for y in range(size):
			column.append(value)

		matrix.append(column)

	return matrix


def encode_position(x, y):
	return x * STATE["size"] + y


def decode_x(position):
	return position // STATE["size"]


def decode_y(position):
	return position % STATE["size"]


def initialise_body():
	global BODY
	size = STATE["size"]

	BODY = []

	for x in range(size):
		column = []

		for y in range(size):
			column.append(False)

		BODY.append(column)


def initialise_hamiltonian():
	global HAMILTONIAN
	global HAM_INDEX
	size = STATE["size"]

	HAMILTONIAN = []
	HAM_INDEX = []

	for x in range(size):
		direction_column = []
		index_column = []

		for y in range(size):
			direction_column.append(0)
			index_column.append(0)

		HAMILTONIAN.append(direction_column)
		HAM_INDEX.append(index_column)

	# Build the same Hamiltonian cycle as action_per_tile().
	for x in range(size):
		for y in range(size):

			if x == 0 and y == 0:
				HAMILTONIAN[x][y] = North

			elif y == 0:
				HAMILTONIAN[x][y] = West

			elif x == size - 1:
				HAMILTONIAN[x][y] = South

			elif x % 2 == 0:
				if y == size - 1:
					HAMILTONIAN[x][y] = East
				else:
					HAMILTONIAN[x][y] = North

			else:
				if y == 1:
					HAMILTONIAN[x][y] = East
				else:
					HAMILTONIAN[x][y] = South

	# Walk the cycle once and assign every tile an index.
	x = 0
	y = 0

	for index in range(size * size):
		HAM_INDEX[x][y] = index

		direction = HAMILTONIAN[x][y]

		if direction == North:
			y += 1

		elif direction == South:
			y -= 1

		elif direction == East:
			x += 1

		elif direction == West:
			x -= 1


def reset_dino_state():
	STATE["apple_x"] = -1
	STATE["apple_y"] = -1
	STATE["length"] = 0
	STATE["active"] = True
	STATE["size"] = get_world_size()
	STATE["capacity"] = STATE["size"] * STATE["size"]
	STATE["steps_without_apple"] = 0

	# A non-wrapping odd square has no Hamiltonian cycle.
	if STATE["size"] < 2 or STATE["size"] % 2 != 0:
		STATE["active"] = False
		return

	initialise_body()
	initialise_hamiltonian()

	# Allocate enough queue space for the whole board.
	new_tail = queue.create_circular_queue(STATE["capacity"])

	TAIL["capacity"] = new_tail["capacity"]
	TAIL["queue"] = new_tail["queue"]
	TAIL["head"] = new_tail["head"]
	TAIL["tail"] = new_tail["tail"]
	TAIL["size"] = new_tail["size"]


def tail_front():
	if TAIL["size"] == 0:
		return -1

	return TAIL["queue"][TAIL["head"]]


def destination_x(direction):
	x = get_pos_x()

	if direction == East:
		x += 1

	elif direction == West:
		x -= 1

	return x


def destination_y(direction):
	y = get_pos_y()

	if direction == North:
		y += 1

	elif direction == South:
		y -= 1

	return y


def safe_direction(direction, growing):
	x = destination_x(direction)
	y = destination_y(direction)

	size = STATE["size"]

	if x < 0:
		return False

	if x >= size:
		return False

	if y < 0:
		return False

	if y >= size:
		return False

	# Tile is not currently occupied.
	if not BODY[x][y]:
		return True

	# The oldest tail segment disappears on a normal move.
	if not growing:
		oldest = tail_front()

		if oldest != -1:
			if encode_position(x, y) == oldest:
				return True

	return False


def hamiltonian_direction():
	return HAMILTONIAN[get_pos_x()][get_pos_y()]


def cycle_distance(start_index, end_index):
	# Forward distance around the Hamiltonian cycle.
	if end_index >= start_index:
		return end_index - start_index

	return STATE["capacity"] - start_index + end_index


def hamiltonian_shortcut_safe(x, y, growing):
	head_x = get_pos_x()
	head_y = get_pos_y()

	head_index = HAM_INDEX[head_x][head_y]
	target_index = HAM_INDEX[x][y]
	target_distance = cycle_distance(head_index, target_index)
	if target_distance == 0:
		return False
	# As the board fills, stop cutting across unused cycle sections.
	# Leave space to grow and let the tail settle onto the full cycle.
	if STATE["length"] + 1 >= STATE["capacity"] // 2:
		if target_distance != 1:
			return False

	# Without a known apple, follow the cycle to discover one.
	apple_x = STATE["apple_x"]
	apple_y = STATE["apple_y"]
	if apple_x < 0 or apple_y < 0:
		if target_distance != 1:
			return False
	else:
		# Never skip the food in cycle order. Tail safety alone allows
		# endless short loops which keep overtaking the same apple.
		apple_index = HAM_INDEX[apple_x][apple_y]
		apple_distance = cycle_distance(head_index, apple_index)
		if target_distance > apple_distance:
			return False

	if TAIL["size"] == 0:
		if growing and target_distance > 1:
			return STATE["capacity"] - target_distance > 4
		return True

	oldest = tail_front()

	tail_x = decode_x(oldest)
	tail_y = decode_y(oldest)

	tail_index = HAM_INDEX[tail_x][tail_y]

	# Distance forward from the head to the tail.
	tail_distance = cycle_distance(head_index, tail_index)
	# Keep a growth buffer when cutting across the cycle. Ordinary
	# successor moves remain available while the tail closes old gaps.
	if target_distance > 1:
		buffer = 3
		if growing:
			buffer += 1
		if tail_distance - target_distance <= buffer:
			return False

	# The shortcut must stay before the tail in Hamiltonian order.
	#
	# If we are not growing, moving onto the oldest tail tile is
	# allowed because that segment disappears during the move.
	if not growing:
		if target_distance <= tail_distance:
			return True

	# When growing, the tail does not move.
	else:
		if target_distance < tail_distance:
			return True

	return False


def candidate_is_safe(direction, growing):
	if not safe_direction(direction, growing):
		return False

	x = destination_x(direction)
	y = destination_y(direction)

	return hamiltonian_shortcut_safe(x, y, growing)


def apple_distance(x, y):
	# Rank progress along the cycle, not geometric closeness to the apple.
	if STATE["apple_x"] < 0 or STATE["apple_y"] < 0:
		return STATE["capacity"]
	return cycle_distance(HAM_INDEX[x][y], HAM_INDEX[STATE["apple_x"]][STATE["apple_y"]])


def shortcut_direction(growing):
	x = get_pos_x()
	y = get_pos_y()

	best_direction = 0
	best_distance = STATE["capacity"] + STATE["capacity"]

	# North
	if candidate_is_safe(North, growing):
		distance = apple_distance(x, y + 1)

		if distance < best_distance:
			best_distance = distance
			best_direction = North

	# East
	if candidate_is_safe(East, growing):
		distance = apple_distance(x + 1, y)

		if distance < best_distance:
			best_distance = distance
			best_direction = East

	# South
	if candidate_is_safe(South, growing):
		distance = apple_distance(x, y - 1)

		if distance < best_distance:
			best_distance = distance
			best_direction = South

	# West
	if candidate_is_safe(West, growing):
		distance = apple_distance(x - 1, y)

		if distance < best_distance:
			best_distance = distance
			best_direction = West

	return best_direction


def remove_oldest_tail():
	if TAIL["size"] == 0:
		return

	position = queue.dequeue(TAIL)

	x = decode_x(position)
	y = decode_y(position)

	BODY[x][y] = False


def add_tail(x, y):
	position = encode_position(x, y)

	queue.enqueue(TAIL, position)

	BODY[x][y] = True


def perform_dino_move(direction, eating_apple):
	old_x = get_pos_x()
	old_y = get_pos_y()

	if not move(direction):
		return False

	# Normal movement advances the tail.
	if not eating_apple:
		if STATE["length"] > 0:
			remove_oldest_tail()

	# Apple movement grows the tail.
	else:
		STATE["length"] += 1

	# Old head becomes the newest tail piece.
	if STATE["length"] > 0:
		add_tail(old_x, old_y)

	return True


def fallback_direction(growing):
	# The normal Hamiltonian successor should always be
	# preferred when no useful shortcut exists.
	direction = hamiltonian_direction()

	if candidate_is_safe(direction, growing):
		return direction

	# These should rarely be needed.
	if candidate_is_safe(North, growing):
		return North

	if candidate_is_safe(East, growing):
		return East

	if candidate_is_safe(South, growing):
		return South

	if candidate_is_safe(West, growing):
		return West

	return 0


def dino_walk():
	if not STATE["active"]:
		reset_dino_state()
		if not STATE["active"]:
			return False

	eating_apple = get_entity_type() == Entities.Apple

	# measure() on the current apple gives the next apple.
	if eating_apple:
		pos = measure()
		if pos == None:
			STATE["active"] = False
			return False

		STATE["apple_x"] = pos[0]
		STATE["apple_y"] = pos[1]
		STATE["steps_without_apple"] = 0
	else:
		# One full cycle must find food. Stop if no apple was spawned
		# (for example, cactus ran out), rather than orbiting forever.
		STATE["steps_without_apple"] += 1
		if STATE["steps_without_apple"] > STATE["capacity"]:
			STATE["active"] = False
			return False

	# Always look for a Hamiltonian-safe shortcut.
	#
	# Long tails use only the ordinary cycle successor.
	direction = shortcut_direction(eating_apple)

	if direction != 0:
		if perform_dino_move(direction, eating_apple):
			return True

	# If no shortcut is available, continue along the cycle.
	direction = fallback_direction(eating_apple)

	if direction == 0:
		STATE["active"] = False
		return False

	if perform_dino_move(direction, eating_apple):
		return True

	STATE["active"] = False
	return False
