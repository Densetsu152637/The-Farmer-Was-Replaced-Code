import util


def cross_tiles(centre):
    size = get_world_size()
    x = centre[0] % size
    y = centre[1] % size
    return [
        (x, y),
        (x, (y + 1) % size),
        ((x + 1) % size, y),
        (x, (y - 1) % size),
        ((x - 1) % size, y),
    ]


def generate_cross_centres():
    # Greedily reserve complete crosses, including across wrapped edges.
    # This is a deterministic maximal packing, not necessarily a maximum one.
    size = get_world_size()
    centres = []
    if size < 3:
        return centres
    occupied = set()
    for y in range(size):
        for x in range(size):
            tiles = cross_tiles((x, y))
            overlaps = False
            for tile in tiles:
                if tile in occupied:
                    overlaps = True
            if not overlaps:
                centres.append((x, y))
                for tile in tiles:
                    occupied.add(tile)
    return centres


def substance_needed():
    return util.lacks_item(Items.Weird_Substance) and util.has_some(Items.Power)


def wait_for_grass():
    while not can_harvest():
        if not substance_needed():
            return False
    return substance_needed()


def substance_cross_action(centre):
    if get_world_size() < 3 or not substance_needed():
        return
    tiles = cross_tiles(centre)
    # Remove old plants (including possibly infected grass), so toggling
    # infection always starts from healthy grass and never creates a maze.
    for tile in tiles:
        if not substance_needed():
            return
        util.go_to_coord(tile)
        harvest()
        util.till_if_required(Grounds.Grassland)

    while substance_needed():
        # All five plants must exist and be mature before infecting the cross.
        for tile in tiles:
            util.go_to_coord(tile)
            if not wait_for_grass():
                return
        util.go_to_coord(tiles[0])
        if num_items(Items.Weird_Substance) > 0:
            if not use_item(Items.Weird_Substance):
                return
            # Finish the whole infected batch even if another drone reaches
            # the target meanwhile. Never toggle leftover infected grass.
            for tile in tiles:
                util.go_to_coord(tile)
                harvest()
        else:
            # Bootstrap with even a single fertilizer; no reserve is needed.
            if num_items(Items.Fertilizer) < 1:
                return
            if not use_item(Items.Fertilizer):
                return
            harvest()
