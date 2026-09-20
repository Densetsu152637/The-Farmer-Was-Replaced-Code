import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


def load_module(util):
    spec = importlib.util.spec_from_file_location('substance_under_test', Path('src/substance_util.py'))
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {'util': util}):
        spec.loader.exec_module(module)
    return module


class Farm:
    def __init__(self, substance=1, fertilizer=0, target=20):
        self.size = 5
        self.pos = (0, 0)
        self.stock = {'substance': substance, 'fertilizer': fertilizer}
        self.target = target
        self.power = True
        self.tiles = {}
        self.prepared = []
        self.uses = []
        self.crops = []
        self.polls = 0
        self.fail_use = False
        self.stop_wait = False
        self.stop_after_use = False
        util = types.SimpleNamespace(
            lacks_item=lambda item: self.stock[item] < self.target,
            shortage_of=lambda item: not self.power,
            go_to_coord=self.move,
            till_if_required=self.prepare,
        )
        self.module = load_module(util)
        self.module.Items = types.SimpleNamespace(Weird_Substance='substance', Fertilizer='fertilizer', Power='power')
        self.module.Grounds = types.SimpleNamespace(Grassland='grassland')
        self.module.get_world_size = lambda: self.size
        self.module.num_items = lambda item: self.stock[item]
        self.module.harvest = self.harvest
        self.module.can_harvest = self.ready
        self.module.use_item = self.use

    def move(self, pos):
        assert all(0 <= v < self.size for v in pos)
        self.pos = pos

    def prepare(self, ground):
        self.prepared.append(self.pos)

    def ready(self):
        self.polls += 1
        assert self.polls < 1000, 'worker failed to terminate'
        if self.stop_wait:
            self.power = False
            return False
        tile = self.tiles.setdefault(self.pos, [False, 0])
        tile[1] += 1
        return tile[1] >= 2

    def harvest(self):
        tile = self.tiles.pop(self.pos, None)
        if tile and tile[0]:
            assert tile[1] >= 2, 'infected grass harvested before maturity'
            self.stock['substance'] += 2
            self.crops.append(self.pos)
        return tile is not None

    def use(self, item):
        if self.fail_use or self.stock[item] == 0:
            return False
        self.stock[item] -= 1
        self.uses.append((item, self.pos))
        if item == 'substance':
            for pos in self.module.cross_tiles(self.pos):
                tile = self.tiles[pos]
                assert tile[1] >= 2
                assert not tile[0], 'toggle would cure an infected plant'
                tile[0] = True
        else:
            self.tiles[self.pos][0] = True
        if self.stop_after_use:
            self.target = 0
            self.power = False
        return True


class SubstanceTests(unittest.TestCase):
    def test_layout_disjoint_wrapped_and_maximal(self):
        module = load_module(types.SimpleNamespace())
        for size in range(1, 65):
            module.get_world_size = lambda: size
            centres = module.generate_cross_centres()
            self.assertEqual(centres, module.generate_cross_centres())
            if size < 3:
                self.assertEqual(centres, [])
                continue
            occupied = set()
            for x, y in centres:
                tiles = {(x, y), (x, (y+1)%size), ((x+1)%size, y), (x, (y-1)%size), ((x-1)%size, y)}
                self.assertEqual(len(tiles), 5)
                self.assertTrue(occupied.isdisjoint(tiles))
                occupied.update(tiles)
            for y in range(size):
                for x in range(size):
                    self.assertTrue(occupied.intersection(module.cross_tiles((x, y))))

    def test_multiple_cycles_from_single_seed(self):
        farm = Farm()
        farm.module.substance_cross_action((0, 0))
        self.assertGreaterEqual(farm.stock['substance'], farm.target)
        self.assertEqual(set(farm.prepared), set(farm.module.cross_tiles((0, 0))))
        self.assertEqual(len(farm.prepared), 5)
        self.assertGreater(len(farm.uses), 1)
        self.assertTrue(all(pos == (0, 0) for _, pos in farm.uses))
        self.assertEqual(len(farm.crops), 5 * len(farm.uses))

    def test_bootstrap_one_fertilizer_then_duplicate(self):
        farm = Farm(substance=0, fertilizer=1)
        farm.module.substance_cross_action((4, 4))
        self.assertEqual(farm.uses[0], ('fertilizer', (4, 4)))
        self.assertTrue(any(item == 'substance' for item, _ in farm.uses))
        self.assertGreaterEqual(farm.stock['substance'], farm.target)

    def test_no_supplies_and_failed_use_return(self):
        for farm in (Farm(0, 0), Farm(1, 0), Farm(0, 1)):
            farm.fail_use = True
            farm.module.substance_cross_action((0, 0))
            self.assertEqual(farm.uses, [])
            self.assertEqual(farm.crops, [])

    def test_no_work_when_target_met_or_power_low(self):
        for farm in (Farm(target=1), Farm()):
            farm.power = False
            farm.module.substance_cross_action((0, 0))
            self.assertEqual(farm.prepared, [])
        farm = Farm(target=1)
        farm.module.substance_cross_action((0, 0))
        self.assertEqual(farm.prepared, [])

    def test_growth_wait_observes_power(self):
        farm = Farm()
        farm.stop_wait = True
        farm.module.substance_cross_action((0, 0))
        self.assertEqual(farm.polls, 1)
        self.assertEqual(farm.uses, [])

    def test_finishes_infected_batch_after_stop(self):
        farm = Farm()
        farm.stop_after_use = True
        farm.module.substance_cross_action((0, 0))
        self.assertEqual(len(farm.crops), 5)
        self.assertEqual(len(farm.uses), 1)

    def test_discards_preexisting_infection(self):
        farm = Farm()
        farm.tiles = {pos: [True, 2] for pos in farm.module.cross_tiles((0, 0))}
        farm.module.substance_cross_action((0, 0))
        self.assertGreaterEqual(farm.stock['substance'], farm.target)


if __name__ == '__main__':
    unittest.main()
