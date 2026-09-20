TARGET_ITEMS = {}
MIN_ITEM = 100000
# Relative effort per missing item, not measured farming times. Includes rough
# input/setup effort and limited parallelism for treasure and dinosaurs.
UPGRADE_ITEM_WEIGHTS = {
	Items.Hay: 1,
	Items.Wood: 2,
	Items.Carrot: 3,
	Items.Power: 4,
	Items.Pumpkin: 5,
	Items.Cactus: 6,
	Items.Weird_Substance: 8,
	Items.Gold: 12,
	Items.Bone: 20
}

ALL_FARMABLE_ITEMS = [
	Items.Hay,
	Items.Wood,
	Items.Carrot,
	Items.Power,
	Items.Pumpkin,
	Items.Cactus,
	Items.Bone,
	Items.Gold,
	Items.Weird_Substance
]

# Place this inside your globals.py file
UPGRADES_LIST = [
	# --- Code & Logic ---
	Unlocks.Loops,
	Unlocks.Variables,
	Unlocks.Functions,
	Unlocks.Lists,
	Unlocks.Dictionaries,
	Unlocks.Import,
	Unlocks.Operators,
	Unlocks.Senses,
	Unlocks.Timing,
	Unlocks.Utilities,
	Unlocks.Costs,
	
	# --- Crops & Farming ---
	Unlocks.Plant,
	Unlocks.Grass,
	Unlocks.Carrots,
	Unlocks.Watering,
	Unlocks.Trees,
	Unlocks.Sunflowers,
	Unlocks.Pumpkins,
	Unlocks.Cactus,
	Unlocks.Dinosaurs,
	Unlocks.Fertilizer,
	Unlocks.Polyculture,
	
	# --- Drone & Progression ---
	Unlocks.Expand,
	Unlocks.Speed,
	Unlocks.Megafarm,
	Unlocks.Mazes,
	Unlocks.Hats,
	Unlocks.Top_Hat,
	Unlocks.Auto_Unlock,
	Unlocks.Leaderboard,
	Unlocks.The_Farmers_Remains
]


