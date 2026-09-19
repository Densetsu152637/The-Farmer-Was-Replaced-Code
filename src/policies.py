import planting
import queue
import util
import sunflower_util
import cacti_util
import substance_util
import treasure_util
import dino_util
import heap
import pumpkin_util

def sufficient_power():
	return not util.shortage_of(Items.Power)

# finished
def power_policy():	
    
	def sunflower_region(region):
		local_petals = heap.create_heap()
		util.action_per_region(planting.farm_sunflower_worker(local_petals), region)
		return local_petals
  
	def go_to_and_harvest(value):
		util.go_to_coord(value[1])
		while not can_harvest():
			continue
		harvest()
    
	while util.lacks_item(Items.Power): 
		# plant all initial sunflowers
		heaps = util.run_parallel_regions(sunflower_region)
		# Heap/reduction state belongs to the parent drone; rebuild it after
		# workers finish so the best-petal harvest is globally coordinated.
		known_petals = heap.heap_merge(heaps)

		# harvest maximum sunflowers in parallel		
		while known_petals["size"] > 0:
			max_petals = sunflower_util.extract_duplicate_max_values(known_petals)		
			util.parallel_map(go_to_and_harvest, max_petals)

# finished
def hay_policy():
    
	def hay_region(region):
		while util.lacks_item(Items.Hay) and sufficient_power():
			util.action_per_region(planting.farm_hay_tile, region)
    
	util.run_parallel_regions(hay_region)
		
# finished
def wood_policy():
    
	def wood_region(region):
		while util.lacks_item(Items.Wood) and sufficient_power():
			util.action_per_region(planting.farm_wood_tile, region)
  
	util.run_parallel_regions(wood_region)
		
# finished		
def carrot_policy():
  
	def carrot_region(region):
		while util.lacks_item(Items.Carrot) and not util.shortage_of(Items.Hay) and not util.shortage_of(Items.Wood) and sufficient_power():
			util.action_per_region(planting.farm_carrot_tile, region)
	  
	util.run_parallel_regions(carrot_region)		
		
# in-progress
def pumpkin_policy():	
	while util.lacks_item(Items.Pumpkin) and not util.shortage_of(Items.Carrot) and sufficient_power():
		# plant all initial pumpkins
		# Planting is independent by row; the queue/giant-pumpkin phase below
		# remains serialized so no two drones replant the same tile.
		util.run_parallel_regions(planting.farm_pumpkin)
		# Region workers repair/check one disjoint band each. The parent repeats
		# rounds until every worker reports readiness, then performs one harvest.
		pending = []
		results = util.parallel_map(pumpkin_util.pumpkin_region, util.region_bounds(max_drones()))
		for result in results:
			if result == None:
				return False
			if result == True or result == False:
				continue
			for coord in result:
				pending.append(coord)
		while len(pending) > 0:
			chunks = []
			count = max_drones()
			for i in range(count):
				x0 = (len(pending) * i) // count
				x1 = (len(pending) * (i + 1)) // count
				if x0 < x1:
					chunks.append(pending[x0:x1])
			results = util.parallel_map(pumpkin_util.pumpkin_pending_region, chunks)
			pending = []
			for result in results:
				if result == None:
					return False
				if result == True or result == False:
					continue
				for coord in result:
					pending.append(coord)

		# harvest giant pumpkin
		harvest()
		util.reposition()

# in-progress
def cactus_policy():
	while util.lacks_item(Items.Cactus) and sufficient_power():
		# Step 1: Plant the entire grid with cactus
		# Cactus sorting is global, but row ownership makes planting safe.
		util.run_parallel_regions(planting.plant_cactus)
		
		# Step 2: Queue all coordinates to monitor maturity
		util.go_to_coord((0, 1))
		while not can_harvest():
			continue
		
		# Step 3: Sort the grid repeatedly until it is perfectly ordered and turns green
		cacti_util.sort_cactus_grid()
		
		# Step 4: Harvest a single tile to trigger the massive recursive chain reaction
		util.go_to_coord((0, 0))
		harvest()
		
		# Final reset/cleanup pass
		util.reposition()
		
# in-progress	
def weird_substance_policy():
	while util.lacks_item(Items.Weird_Substance) and util.has_some(Items.Fertilizer) and sufficient_power():
		results = util.parallel_map(substance_util.substance_worker,
			util.region_bounds(max_drones()))
		failed = False
		for result in results:
			if result == None:
				failed = True
				break
		util.reposition()
		if failed:
			break

# in-progress
def treasure_policy():
	world = get_world_size()
	upgrade = num_unlocked(Unlocks.Mazes)
	if upgrade < 1:
		upgrade = 1
	maze_amount = world * 2 ** (upgrade - 1)
	# One fresh full-field maze is acyclic. Workers own disjoint DFS branches;
	# none may harvest, so the parent can join all workers before one harvest.
	util.reposition()
	util.harvest_if()
	util.till_if_required(Grounds.Soil)
	if not plant(Entities.Bush):
		return False
	if not use_item(Items.Weird_Substance, maze_amount):
		return False
	directions = [North, East, South, West]
	root_jobs = []
	for direction in directions:
		if not can_move(direction):
			continue
		root_jobs.append(direction)
	results = util.parallel_map(treasure_util.maze_branch_worker, root_jobs)
	route = None
	for result in results:
		if route == None:
			route = result
	if route == None:
		return False
	for direction in route:
		move(direction)
	if get_entity_type() == Entities.Treasure:
		harvest()
	util.reposition()
	return True
		
# finished
def dinosaur_policy():
	# Pre-flight checks.
	util.reset_farm()

	while (
		util.lacks_item(Items.Bone)
		and not util.shortage_of(Items.Cactus)
		and sufficient_power()
	):
		# Start a fresh dinosaur game.
		change_hat(Hats.Dinosaur_Hat)
		dino_util.reset_dino_state()

		# dino_walk() performs one move at a time.
		while dino_util.dino_walk():
			continue

		# Removing the dinosaur hat harvests the tail.
		change_hat(Hats.Straw_Hat)
