import unittest

from services.decision_service import build_decision


class DecisionServiceTest(unittest.TestCase):
    def test_balanced_preset_uses_overall_score_thresholds(self):
        cases = [
            (0.85, "high_similarity", "high", True),
            (0.70, "medium_similarity", "medium", True),
            (0.55, "low_similarity", "low", False),
            (0.54, "no_significant_similarity", "very_low", False),
        ]

        for score, expected_status, expected_risk, requires_review in cases:
            with self.subTest(score=score):
                result = build_decision(
                    overall_score=score,
                    clip_score=0.99,
                    cnn_score=0.99,
                    preset="balanced",
                )

                self.assertEqual(result["decision"]["status"], expected_status)
                self.assertEqual(result["decision"]["risk_level"], expected_risk)
                self.assertIs(
                    result["decision"]["requires_review"],
                    requires_review,
                )

    def test_detail_scores_do_not_override_overall_score_category(self):
        result = build_decision(
            overall_score=0.54,
            clip_score=0.99,
            cnn_score=0.99,
            preset="balanced",
        )

        self.assertEqual(
            result["decision"]["status"],
            "no_significant_similarity",
        )
        self.assertEqual(result["clip_score"], 0.99)
        self.assertEqual(result["cnn_score"], 0.99)

    def test_custom_thresholds_are_the_only_decision_boundaries(self):
        thresholds = {
            "high": 0.90,
            "medium": 0.80,
            "low": 0.60,
        }

        result = build_decision(
            overall_score=0.75,
            clip_score=0.99,
            cnn_score=0.99,
            custom_thresholds=thresholds,
        )

        self.assertEqual(result["decision"]["status"], "low_similarity")
        self.assertIn("mode custom", result["decision"]["reason"])


if __name__ == "__main__":
    unittest.main()
