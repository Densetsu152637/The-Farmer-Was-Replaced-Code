import planting
import queue
import util
import sunflower_util
import cacti_util
import substance_util
import treasure_util
import dino_util
import heap

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
		
  
# finished
def pumpkin_policy():	
	
	def pumpkin_plant_region(region):
		util.action_per_region(planting.farm_pumpkin, region)
		# go through the pumpkins and replace broken ones with fresh ones
		dead_pumpkins = queue.create_circular_queue(region["size"][0] * region["size"][1])
		for pos in util.generate_tile_sequence(region["start"], region["size"]):
			queue.enqueue(dead_pumpkins, pos)
		
		while dead_pumpkins["size"] > 0:
			next_tile = queue.dequeue(dead_pumpkins)
			util.go_to_coord(next_tile)
   
			# If a pumpkin died, replant it and put it back in the queue to check later
			if get_entity_type() == Entities.Dead_Pumpkin:
				harvest()
				plant(Entities.Pumpkin)
				util.water_if_possible()
				queue.enqueue(dead_pumpkins, next_tile)
				
			# If it is alive but NOT ready to harvest, skip it for now and re-queue it
			elif not can_harvest():
				queue.enqueue(dead_pumpkins, next_tile)
				
			# If can_harvest() is true and it's not dead, it's fully grown! 
			# Leave it standing so it can merge into a giant pumpkin.
			else:
				pass 	

		# all pumpkins are ready to be harvested (one giant one)

	
	while util.lacks_item(Items.Pumpkin) and not util.shortage_of(Items.Carrot) and sufficient_power():
		# plant all initial pumpkins
		# Planting is independent by row; the queue/giant-pumpkin phase below
		# remains serialized so no two drones replant the same tile.
		util.run_parallel_regions(pumpkin_plant_region)
		# harvest giant pumpkin			
		util.go_to(0, 0)
		harvest()


# finished
def cactus_policy():
    
	def cactus_plant_region(region):
		util.action_per_region(planting.farm_cactus, region)
    
	while util.lacks_item(Items.Cactus) and sufficient_power():
		# Step 1: Plant the entire grid with cactus
		# Cactus sorting is global, but row ownership makes planting safe.
		util.run_parallel_regions(cactus_plant_region)
		
		# Step 2: Queue all coordinates to monitor maturity
		util.go_to(0, 1)
		while not can_harvest():
			continue
		
		# Step 3: Sort the grid repeatedly until it is perfectly ordered and turns green
		cacti_util.sort_cactus_grid()
		
		# Step 4: Harvest a single tile to trigger the massive recursive chain reaction
		util.go_to(0, 0)
		harvest()
		
  
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


# finished
def treasure_policy():
	# Repeat complete create/search/join/harvest runs until the gold target.
	while util.lacks_item(Items.Gold) and not util.lacks_item(Items.Weird_Substance) and util.has_some(Items.Fertilizer) and sufficient_power():
		if not treasure_util.create_maze():
			return False
		if not treasure_util.solve_maze():
			return False
	return not util.lacks_item(Items.Gold)


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
