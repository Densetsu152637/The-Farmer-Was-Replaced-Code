import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


class UpgradeTests(unittest.TestCase):
    def setUp(self):
        self.config = types.SimpleNamespace(
            ALL_FARMABLE_ITEMS=['hay', 'wood', 'gold', 'bone'],
            UPGRADE_ITEM_WEIGHTS={'hay': 1, 'wood': 2, 'gold': 12, 'bone': 20},
            UPGRADES_LIST=[], TARGET_ITEMS={'stale': 1}, MIN_ITEM=10)
        spec = importlib.util.spec_from_file_location('upgrade_under_test', Path('src/upgrade_util.py'))
        self.module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'globals': self.config}):
            spec.loader.exec_module(self.module)
        self.costs = {}
        self.stock = {}
        self.locked = set()
        self.attempts = []
        self.module.get_cost = lambda upgrade: self.costs[upgrade]
        self.module.num_items = lambda item: self.stock.get(item, 0)
        self.module.num_unlocked = lambda item: int(item not in self.locked)
        self.module.unlock = self.purchase

    def purchase(self, upgrade):
        self.attempts.append(upgrade)
        for item, amount in self.costs[upgrade].items():
            self.stock[item] -= amount
        self.costs[upgrade] = None
        return True

    def candidates(self, costs):
        self.costs = costs
        self.config.UPGRADES_LIST = list(costs)

    def test_weights_and_mixed_costs(self):
        self.candidates({'bones': {'bone': 10}, 'treasure': {'gold': 10},
                         'mixed': {'hay': 30, 'wood': 20}})
        self.assertEqual(self.module.get_next_cheapest_upgrade()[0], 'mixed')

    def test_inventory_changes_choice_and_surplus_does_not_cancel_shortage(self):
        self.candidates({'large': {'bone': 100}, 'small': {'hay': 50}})
        self.stock['bone'] = 99
        self.assertEqual(self.module.get_next_cheapest_upgrade()[0], 'large')
        self.assertEqual(self.module.upgrade_score({'bone': 1, 'hay': 50})[0], 50)

    def test_unavailable_resources_skip_unless_already_owned(self):
        self.candidates({'unknown': {'trophy': 1}, 'locked': {'bone': 1}})
        self.locked.add('bone')
        self.assertIsNone(self.module.get_next_cheapest_upgrade())
        self.stock['trophy'] = 1
        self.assertEqual(self.module.get_next_cheapest_upgrade()[0], 'unknown')

    def test_ties_use_total_spend_then_list_order(self):
        self.candidates({'expensive': {'bone': 2}, 'first': {'hay': 20}, 'second': {'hay': 20}})
        self.stock['bone'] = 1
        self.assertEqual(self.module.get_next_cheapest_upgrade()[0], 'first')

    def test_purchases_recalculate_after_spending(self):
        self.candidates({'first': {'hay': 20}, 'second': {'hay': 25}})
        self.stock['hay'] = 30
        self.module.update_target_items_for_upgrades()
        self.assertEqual(self.attempts, ['first'])
        self.assertEqual(self.config.TARGET_ITEMS['hay'], 25)
        self.assertNotIn('stale', self.config.TARGET_ITEMS)

    def test_failed_purchase_does_not_loop_and_can_retry_after_progress(self):
        self.candidates({'blocked': {'hay': 1}, 'prerequisite': {'hay': 2}})
        self.stock['hay'] = 10
        def unlock(upgrade):
            if upgrade == 'blocked' and self.costs['prerequisite'] is not None:
                self.attempts.append(upgrade)
                return False
            return self.purchase(upgrade)
        self.module.unlock = unlock
        self.module.update_target_items_for_upgrades()
        self.assertEqual(self.attempts, ['blocked', 'prerequisite', 'blocked'])

    def test_all_failed_terminates(self):
        self.candidates({'blocked': {'hay': 1}})
        self.stock['hay'] = 1
        def fail(upgrade):
            self.attempts.append(upgrade)
            self.assertLess(len(self.attempts), 2)
            return False
        self.module.unlock = fail
        self.module.update_target_items_for_upgrades()
        self.assertEqual(self.attempts, ['blocked'])

    def test_free_and_completed_upgrades(self):
        self.candidates({'done': None, 'free': {}})
        self.module.update_target_items_for_upgrades()
        self.assertEqual(self.attempts, ['free'])

    def test_targets_are_unweighted_totals_with_minimum_floor(self):
        self.candidates({'next': {'hay': 5, 'bone': 30, 'trophy': 1}})
        self.stock = {'bone': 29, 'trophy': 1}
        self.module.update_target_items_for_upgrades()
        self.assertEqual(self.config.TARGET_ITEMS, {'hay': 10, 'wood': 10, 'gold': 10, 'bone': 30})


if __name__ == '__main__':
    unittest.main()
