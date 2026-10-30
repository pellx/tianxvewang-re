import math
import struct
import tempfile
import unittest
from pathlib import Path

from oral_scoring.formulas import (completion_score, fluency_postprocess, frame_gop,
    long_sentence_score, normalize, ordinary_word_score, paragraph_score,
    phone_gop, phone_score, rbf_svr_predict)
from oral_scoring.models import SvrModel, read_payload


class ScoringTests(unittest.TestCase):
    def test_word_sample(self):
        self.assertAlmostEqual(ordinary_word_score([51.95, 59.36, 61.81, 88.22, 86.22]), 69.512)

    def test_completion_branches_and_half_boundary(self):
        self.assertEqual(completion_score(10, 3, 2), 70)
        self.assertEqual(completion_score(10, 3, 5), 70)
        self.assertEqual(completion_score(10, 3, 6), 40)

    def test_phone_pipeline(self):
        self.assertEqual(phone_gop([frame_gop(-2, 1), frame_gop(-4, 1)]), 3)
        self.assertEqual(phone_score(3, 5, 1), 60)
        self.assertEqual(phone_score(5, 5, 1), 100)
        self.assertEqual(phone_score(0, 5, 1), 0)

    def test_long_sentence_and_low_completion(self):
        self.assertAlmostEqual(long_sentence_score(78.87, 100, 100), 83.096)
        self.assertAlmostEqual(long_sentence_score(80, 90, 40), 82 * 40 / 75)

    def test_svr_sparse_and_standardization(self):
        z = normalize([2, 4], [1, 2], [1, 2])
        predicted = rbf_svr_predict(z, 0.5, -0.25, [(2, {1: 1}), (-1, {1: 1, 2: 1})])
        self.assertAlmostEqual(predicted, 2 * math.exp(-0.5) - 1 + 0.25)

    def test_fluency_postprocess(self):
        self.assertEqual(fluency_postprocess(8, 10, 1), 85)
        self.assertEqual(fluency_postprocess(9, 10, 1), 100)
        self.assertEqual(fluency_postprocess(6, 10, 0), 0)

    def test_candidate_paragraph(self):
        coeff = [0.77266539, 0.05508793, 0.18843264, -23.51403671, -15.79654803]
        result = paragraph_score([68.10014925373136, 100, 92.025, 0, 18 / 99], coeff, 0.1992771)
        self.assertAlmostEqual(result, 72.79511253637436)

    def test_inputs_reject_unsupported(self):
        with self.assertRaises(ValueError):
            phone_gop([])
        with self.assertRaises(ValueError):
            completion_score(0, 0, 0)
        with self.assertRaises(ValueError):
            normalize([1], [1, 2], [1])

    def test_wrapped_model_loading_and_prediction(self):
        payload = (b"svm_type epsilon_svr\nkernel_type rbf\ngamma 0.5\n"
                   b"nr_class 2\ntotal_sv 2\nrho -0.25\nSV\n"
                   b"2 1:1\n-1 1:1 2:1\n")
        encoded = bytes(b ^ (i % 8 + 1) for i, b in enumerate(payload))
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            path = Path(directory) / "example.model"
            path.write_bytes(b"encr" + struct.pack("<I", len(payload)) + encoded)
            self.assertEqual(read_payload(path), payload)
            model = SvrModel.read(path)
            self.assertAlmostEqual(model.predict([1, 1]), 2 * math.exp(-0.5) - 1 + 0.25)
            path.write_bytes(b"encr" + struct.pack("<I", len(payload) + 1) + encoded)
            with self.assertRaises(ValueError):
                read_payload(path)


if __name__ == "__main__":
    unittest.main()
