"""Regression against an actual held-tool Wolf fold, not synthetic scores."""
import importlib.util
import json
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


class ArchivedFoldTests(unittest.TestCase):
    def test_scalar_adapter_reproduces_archived_decisions(self):
        path = ROOT / 'blta.py'
        self.assertTrue(path.exists(), 'Standalone BLTA scorer is not implemented')
        spec = importlib.util.spec_from_file_location('standalone_blta', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        fixture = np.load(ROOT/'tests/archived_wolf_order.npz', allow_pickle=False)
        model = json.loads((ROOT/'tests/archived_wolf_order.json').read_text())
        head = module.BLTA.from_dict(model['raw'])
        raw = head.scores(fixture['test_features'])
        np.testing.assert_allclose(raw, fixture['raw_scores'], rtol=0, atol=1e-10)
        self.assertEqual(int(np.sum(raw > head.threshold)), 144)
        head.adapt(model['tool'], fixture['target_normal'])
        aligned = head.scores(fixture['test_features'], [model['tool']]*len(raw))
        np.testing.assert_allclose(aligned, fixture['aligned_scores'], rtol=0, atol=1e-10)
        self.assertEqual(int(np.sum(aligned > head.threshold)), 1)
        np.testing.assert_array_equal(head.scores(fixture['test_features'], ['known_source']*len(raw)), raw)
        np.testing.assert_array_equal(np.argsort(raw), np.argsort(aligned))

    def test_cpu_refit_recovers_original_source_model(self):
        path = ROOT / 'blta.py'
        spec = importlib.util.spec_from_file_location('standalone_blta_fit', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(hasattr(module.BLTA, 'fit'), 'CPU source fitting is not implemented')
        fixture = np.load(ROOT/'tests/archived_wolf_order.npz', allow_pickle=False)
        model = json.loads((ROOT/'tests/archived_wolf_order.json').read_text())['raw']
        head = module.BLTA.fit(fixture['source_normal'], fixture['source_attack'], fixture['calibration_normal'])
        np.testing.assert_allclose(head.weight, model['weight'], rtol=0, atol=1e-10)
        self.assertAlmostEqual(head.threshold, model['threshold'], places=10)
        self.assertEqual(int(np.sum(head.blocked(fixture['test_features']))), 144)


if __name__ == '__main__':
    unittest.main()
