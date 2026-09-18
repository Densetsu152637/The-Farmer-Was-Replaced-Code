import planting
import queue
import util
import sunflower_util
import cacti_util
import substance_util
import treasure_util
import dino_util

def sufficient_power():
	return not util.shortage_of(Items.Power)


def power_policy():	
	while util.lacks_item(Items.Power): 
		# plant all initial sunflowers
		util.action_per_tile(planting.plant_sunflower)		
		while sunflower_util.known_petals["size"] > 0:
			next = sunflower_util.get_end()
			coord = next[1]
			util.go_to_coord(coord)
			while not can_harvest():
				continue
			harvest()

def hay_policy():	
	def tile_action():
		util.harvest_if()
		planting.plant_hay()	
	
	while util.lacks_item(Items.Hay) and sufficient_power():
		util.action_per_tile(tile_action)	
		
		
def wood_policy():
	def tile_action():
		util.harvest_if()
		planting.plant_wood()	
	
	while util.lacks_item(Items.Wood) and sufficient_power():
		util.action_per_tile(tile_action)	
		
		
def carrot_policy():
	def tile_action():
		util.harvest_if()
		planting.plant_carrot()	
	
	while util.lacks_item(Items.Carrot) and not util.shortage_of(Items.Hay) and not util.shortage_of(Items.Wood) and sufficient_power():
		util.action_per_tile(tile_action)	
		
		

def pumpkin_policy():	
	while util.lacks_item(Items.Pumpkin) and not util.shortage_of(Items.Carrot) and sufficient_power():
		# plant all initial pumpkins
		util.action_per_tile(planting.plant_pumpkin)	
		# queue all coords to check over
		dead_pumpkins = queue.create_circular_queue(get_world_size() * get_world_size())
		for coord in util.generate_all_tiles():
			queue.enqueue(dead_pumpkins, coord)
			
		# pass over all tiles and cull dead ones
		while dead_pumpkins["size"] > 0:
			# get next pumpkin to check
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
		
		# harvest giant pumpkin
		harvest()	
		util.reposition()
			
			
def cactus_policy():
	while util.lacks_item(Items.Cactus) and sufficient_power():
		# Step 1: Plant the entire grid with cactus
		util.action_per_tile(planting.plant_cactus)
		
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
		
		
def weird_substance_policy():
	def tile_action():
		util.till_if_required(Grounds.Grassland)
	
	util.action_per_tile(tile_action)
	
	while util.lacks_item(Items.Weird_Substance) and util.has_some(Items.Fertilizer) and sufficient_power():
		
		# Step 1: Create a circular queue of all tiles
		tile_queue = queue.create_circular_queue(get_world_size() * get_world_size())
		for coord in util.generate_all_tiles():
			queue.enqueue(tile_queue, coord)
			
		# Step 2: Algorithmic pass to set up the correct states
		while tile_queue["size"] > 0:
			next_tile = queue.dequeue(tile_queue)
			util.go_to_coord(next_tile)
			
			target_state = substance_util.get_weird_substance_requirement() 
			
			if substance_util.current_tile_matches(target_state):
				util.water_if_possible()
			else:
				if can_harvest():
					harvest()
					substance_util.clear_cache_at_current() # FIX: Wipe cache on harvest
				
				substance_util.plant_dynamic(target_state) 
				util.water_if_possible()
				queue.enqueue(tile_queue, next_tile)
				
		# Step 3: Trigger the harvest phase once pattern is complete
		for coord in util.generate_all_tiles():
			util.go_to_coord(coord)
			if can_harvest():
				harvest()
				substance_util.clear_cache_at_current() # FIX: Wipe cache on harvest
				
		util.reposition()


def treasure_policy():
	# Loop runs based on global target checks
	while util.lacks_item(Items.Gold) and util.has_some(Items.Weird_Substance) and sufficient_power():
		
		# Step 1: Manage Maze Instantiation / Upkeep
		if get_entity_type() != Entities.Hedge and get_entity_type() != Entities.Treasure:
			util.harvest_if()
			util.till_if_required(Grounds.Soil)
			plant(Entities.Bush)
			
			size_req = get_world_size()
			if num_items(Items.Weird_Substance) >= size_req:
				use_item(Items.Weird_Substance, size_req)
				treasure_util.clear_maze_memory() # Fresh maze generated, wipe old cache
			else:
				break # Out of Weird Substance, pause execution
		
		# Step 2: Traverse using DFS Graph Mapping
		found_chest = False
		while not found_chest:
			treasure_util.register_visit()
			
			# Check win condition
			if get_entity_type() == Entities.Treasure:
				harvest() # Collect reward!
				found_chest = True
				break
				
			moved = False
			# Loop through the 4 directional options using indices
			for i in range(4):
				d = treasure_util.directions[i]
				
				if can_move(d):
					target_key = treasure_util.get_target_key(d)
					
					if not treasure_util.is_visited(target_key):
						move(d)
						treasure_util.push_return_path(treasure_util.opposite_dirs[i])
						moved = True
						break # Break direction loop to register the new tile
						
			# Step 3: Backtrack if stuck in a loop or dead-end
			if not moved:
				return_dir = treasure_util.pop_return_path()
				if return_dir != None:
					move(return_dir)
				else:
					# Grid exhausted or chest became unreachable
					break
					
		# Step 4: Return cleanly to origin using your optimized helper
		util.reposition()
		

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
		
	



	
	

	
			
		
	

		
	
		
	
	
	
	