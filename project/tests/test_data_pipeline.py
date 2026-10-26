import unittest
import pandas as pd

from src.data_validation import normalize_soc, normalize_task, penetration_weighted_mode, validate_unique
from src.clean_and_join_data import parse_bls_numeric, normalize_bls_categories, missing_value_audit


class PipelineValidationTests(unittest.TestCase):
    def test_soc_normalization(self):
        self.assertEqual(normalize_soc(" 15-1252.00 "), ("15-1252.00", "15-1252"))
        self.assertEqual(normalize_soc("151252"), ("15-1252.00", "15-1252"))
        self.assertEqual(normalize_soc("bad"), (None, None))

    def test_task_normalization(self):
        self.assertEqual(normalize_task("  Create  “AI” tools. "), 'create "ai" tools')
        self.assertEqual(normalize_task("Web"), normalize_task("web"))

    def test_duplicate_detection(self):
        with self.assertRaises(ValueError):
            validate_unique(pd.DataFrame({"soc_code": ["11-1011", "11-1011"]}), ["soc_code"], "fixture")

    def test_penetration_weighted_mode(self):
        tasks = pd.DataFrame({"penetration": [0.2, 0.8], "augmentation_share": [1.0, 0.0], "automation_share": [0.0, 1.0]})
        result = penetration_weighted_mode(tasks)
        self.assertAlmostEqual(result["augmentation_share"], 0.2)
        self.assertAlmostEqual(result["automation_share"], 0.8)
        self.assertEqual(result["dominant_mode"], "automation")

    def test_zero_denominator_is_missing(self):
        tasks = pd.DataFrame({"penetration": [0.0], "augmentation_share": [1.0], "automation_share": [0.0]})
        result = penetration_weighted_mode(tasks)
        self.assertIsNone(result["augmentation_share"])
        self.assertIsNone(result["automation_share"])

    def test_unknown_mode_tasks_are_excluded_from_supported_denominator(self):
        tasks = pd.DataFrame({"penetration": [0.2, 0.8], "augmentation_share": [1.0, None], "automation_share": [0.0, None]})
        result = penetration_weighted_mode(tasks)
        self.assertEqual(result["augmentation_share"], 1.0)
        self.assertEqual(result["automation_share"], 0.0)

    def test_final_key_uniqueness(self):
        validate_unique(pd.DataFrame({"soc_code": ["11-1011", "11-1021"]}), ["soc_code"], "fixture")
        validate_unique(pd.DataFrame({"onet_soc_code": ["11-1011.00", "11-1011.03"], "task_id": ["1", "1"]}), ["onet_soc_code", "task_id"], "fixture")
        with self.assertRaises(ValueError):
            validate_unique(pd.DataFrame({"onet_soc_code": ["11-1011.00", "11-1011.00"], "task_id": ["1", "1"]}), ["onet_soc_code", "task_id"], "fixture")

    def test_bls_numeric_preserves_negative_and_suppression(self):
        parsed = parse_bls_numeric(pd.Series(["-1.2", "1,200", "—", "Suppressed"]))
        self.assertEqual(parsed.iloc[0], -1.2)
        self.assertEqual(parsed.iloc[1], 1200)
        self.assertTrue(pd.isna(parsed.iloc[2]))
        self.assertTrue(pd.isna(parsed.iloc[3]))

    def test_bls_none_labels_are_preserved_field_specifically(self):
        frame = normalize_bls_categories(pd.DataFrame({"related_work_experience": ["None", None], "on_the_job_training": ["None", None]}))
        self.assertEqual(frame.loc[0, "related_work_experience"], "No related work experience required")
        self.assertEqual(frame.loc[0, "on_the_job_training"], "No on-the-job training required")
        self.assertTrue(pd.isna(frame.loc[1, "related_work_experience"]))
        self.assertTrue(pd.isna(frame.loc[1, "on_the_job_training"]))

    def test_missing_value_audit_categorizes_zero_denominator(self):
        audit = missing_value_audit({"occupation": pd.DataFrame({"positive_penetration_task_pct": [None, 0.5]})})
        self.assertEqual(audit.iloc[0].reason_category, "derived metric undefined because denominator is zero")
        self.assertEqual(audit.iloc[0].missing_count, 1)


if __name__ == "__main__":
    unittest.main()
