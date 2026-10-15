"""Reject parameter states that can silently turn blocking into false decisions."""
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from blta import BLTA


class InputValidationTests(unittest.TestCase):
    def head(self, **changes):
        args = dict(mean=[0., 0.], scale=[1., 1.], weight=[1., 0.],
                    bias=0., threshold=.5)
        args.update(changes)
        return BLTA(**args)

    def test_nan_threshold_cannot_silently_admit_every_observation(self):
        with self.assertRaises(ValueError):
            self.head(threshold=np.nan)

    def test_nonfinite_bias_is_rejected(self):
        for value in [np.nan, np.inf, -np.inf]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.head(bias=value)

    def test_nonfinite_tool_offset_is_rejected(self):
        for value in [np.nan, np.inf, -np.inf]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.head(offsets={'tool': value})

    def test_single_tool_string_cannot_be_mistaken_for_per_row_ids(self):
        with self.assertRaises(ValueError):
            self.head().scores([[1., 0.], [2., 0.]], tools='ab')

    def test_imported_offset_keys_use_the_same_canonical_ids_as_scoring(self):
        head = self.head(offsets={1: -2.})
        np.testing.assert_allclose(head.scores([[1., 0.]], [1]), [-1.])

    def test_empty_feature_dimension_is_rejected(self):
        with self.assertRaises(ValueError):
            BLTA([], [], [], 0., .5)

    def test_unbounded_calibration_threshold_remains_supported(self):
        self.assertFalse(self.head(threshold=np.inf).blocked([[10., 0.]])[0])


if __name__ == '__main__':
    unittest.main()
