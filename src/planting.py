import util
import sunflower_util

def plant_hay():
	util.harvest_if_not(Entities.Grass)
	util.till_if_required(Grounds.Grassland)

def plant_wood():
	util.harvest_if_not(Entities.Tree)
	if util.is_even(get_pos_x() + get_pos_y()):
		plant(Entities.Tree)
	else:
		plant(Entities.Bush)
		
def plant_carrot():
	util.harvest_if_not(Entities.Carrot)
	util.till_if_required(Grounds.Soil)
	plant(Entities.Carrot)
	
def plant_pumpkin():
	util.harvest_if_not(Entities.Pumpkin)
	util.till_if_required(Grounds.Soil)
	plant(Entities.Pumpkin)
	
def plant_sunflower():
	util.harvest_if_not(Entities.Sunflower)
	util.till_if_required(Grounds.Soil)	
	# if the tile is blank and ready for a sunflower
	if get_entity_type() != Entities.Sunflower:
		util.till_if_required(Grounds.Soil)
		plant(Entities.Sunflower)
		# read subflower petals and add to sorted list
		sunflower_util.add_to_collection()
		
def plant_cactus():
	util.harvest_if_not(Entities.Cactus)
	util.till_if_required(Grounds.Soil)
	plant(Entities.Cactus)
		
	
	
	