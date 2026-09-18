import util


def pumpkin_region(region):
	x0, y0, x1, y1 = region
	pending = []
	for x in range(x0, x1):
		for y in range(y0, y1):
			util.go_to(x, y)
			entity = get_entity_type()
			if entity != Entities.Pumpkin:
				if entity != None:
					harvest()
				if not plant(Entities.Pumpkin):
					return None
				util.water_if_possible()
				pending.append((x, y))
			elif not can_harvest():
				pending.append((x, y))
	return pending


def pumpkin_pending_region(coords):
	pending = []
	for x, y in coords:
		util.go_to(x, y)
		entity = get_entity_type()
		if entity != Entities.Pumpkin:
			if entity != None:
				harvest()
			if not plant(Entities.Pumpkin):
				return None
			util.water_if_possible()
			pending.append((x, y))
		elif not can_harvest():
			pending.append((x, y))
	return pending
