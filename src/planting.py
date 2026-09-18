import util
import heap

def farm_hay_tile():
	util.harvest_if()
	util.till_if_required(Grounds.Grassland)

def farm_wood_tile():
	util.harvest_if()
	if util.is_even(get_pos_x() + get_pos_y()):
		plant(Entities.Tree)
	else:
		plant(Entities.Bush)
	util.water_if_possible()

def farm_carrot_tile():
	util.harvest_if()
	util.till_if_required(Grounds.Soil)
	plant(Entities.Carrot)
	util.water_if_possible()
	
def farm_pumpkin():
	util.harvest_if_not(Entities.Pumpkin)
	util.till_if_required(Grounds.Soil)
	plant(Entities.Pumpkin)
	
def farm_sunflower_worker(local_petals):
	def f():
		# Worker-safe planting variant: heap state is drone-local, so measurement
		# reduction is deliberately performed by the parent after the join.
		util.harvest_if_not(Entities.Sunflower)
		util.till_if_required(Grounds.Soil)
		if get_entity_type() != Entities.Sunflower:
			plant(Entities.Sunflower)
			util.water_if_possible()
		# Existing sunflowers must also be included in this round's heap.
		value = [measure(), [get_pos_x(), get_pos_y()]]
		heap.heap_push(local_petals, value)
   
	return f
		
def farm_cactus():
	util.harvest_if()
	util.till_if_required(Grounds.Soil)
	plant(Entities.Cactus)



