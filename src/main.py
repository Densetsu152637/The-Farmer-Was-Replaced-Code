import globals
import util
import upgrade_util
import policies

def print_targets():
	for item in globals.TARGET_ITEMS:
		amount = globals.TARGET_ITEMS[item]
		if amount != globals.MIN_ITEM:
			print(str(item) + ": " + str(amount))
			move(North)
	util.go_to(0, 0)
	

POLICIES = {
	Items.Power : policies.power_policy,
	Items.Hay : policies.hay_policy,
	Items.Wood : policies.wood_policy,
	Items.Carrot : policies.carrot_policy,
	Items.Pumpkin : policies.pumpkin_policy,		
	Items.Cactus: policies.cactus_policy,
	Items.Weird_Substance: policies.weird_substance_policy,
	Items.Gold: policies.treasure_policy,
	Items.Bone: policies.dinosaur_policy
}
	
# move to the bottom right corner
util.reset_farm()
	
# start loop
while True:
	upgrade_util.update_target_items_for_upgrades()
	print_targets()
	# get policies
	short = []
	for item in globals.TARGET_ITEMS:
		if util.lacks_item(item):
			short.append(item)
	for item in short:
		print("Getting " + str(item))
		policy = POLICIES[item]
		policy()		
		util.reposition()	
		do_a_flip()
		pet_the_piggy()