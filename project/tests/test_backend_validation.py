import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

import backend_analysis as backend


def occupation_fixture(rows=1):
    data = {
        "soc_code": ["11-1011"] * rows,
        "occupation_title": ["Chief Executive"] * rows,
        "bls_title": ["Chief executives"] * rows,
        "major_group_code": ["11"] * rows,
        "major_group_title": ["Management Occupations"] * rows,
        "observed_exposure": [0.2] * rows,
        "mapped_task_count": [2] * rows,
        "positive_penetration_task_count": [1] * rows,
        "positive_penetration_task_pct": [0.5] * rows,
        "mean_task_penetration": [0.25] * rows,
        "augmentation_share": [np.nan] * rows,
        "automation_share": [np.nan] * rows,
        "dominant_mode": [np.nan] * rows,
        "employment_base_year": [1000] * rows,
        "employment_projection_year": [1100] * rows,
        "employment_change_numeric": [100] * rows,
        "employment_growth_pct": [10] * rows,
        "annual_openings": [50] * rows,
        "median_annual_wage": [80000] * rows,
    }
    return pd.DataFrame(data)


def task_fixture(rows=1):
    return pd.DataFrame({
        "onet_soc_code": ["11-1011.00"] * rows,
        "soc_code": ["11-1011"] * rows,
        "occupation_title": ["Chief Executive"] * rows,
        "task_id": [str(i + 1) for i in range(rows)],
        "task": [f"Direct activity {i + 1}." for i in range(rows)],
        "task_normalized": [f"direct activity {i + 1}" for i in range(rows)],
        "penetration": [0.2] * rows,
        "augmentation_share": [np.nan] * rows,
        "automation_share": [np.nan] * rows,
        "dominant_mode": [np.nan] * rows,
    })


class CanonicalValidationTests(unittest.TestCase):
    def test_valid_canonical_fixtures_pass(self):
        report = backend.validate_spec_alignment(occupation_fixture(), task_fixture())
        self.assertEqual(report["unique_occupations"], 1)
        self.assertEqual(report["task_rows"], 1)

    def test_missing_occupation_task_count_column_fails(self):
        with self.assertRaisesRegex(backend.DataValidationError, "mapped_task_count"):
            backend.validate_spec_alignment(occupation_fixture().drop(columns="mapped_task_count"))

    def test_missing_onet_soc_column_fails(self):
        with self.assertRaisesRegex(backend.DataValidationError, "onet_soc_code"):
            backend.validate_spec_alignment(occupation_fixture(), task_fixture().drop(columns="onet_soc_code"))

    def test_missing_task_id_column_fails(self):
        with self.assertRaisesRegex(backend.DataValidationError, "task_id"):
            backend.validate_spec_alignment(occupation_fixture(), task_fixture().drop(columns="task_id"))

    def test_null_occupation_soc_fails(self):
        df = occupation_fixture(); df.loc[0, "soc_code"] = None
        with self.assertRaisesRegex(backend.DataValidationError, "occupation data.soc_code.*null"):
            backend.validate_spec_alignment(df)

    def test_null_task_soc_fails(self):
        df = task_fixture(); df.loc[0, "soc_code"] = None
        with self.assertRaisesRegex(backend.DataValidationError, "task data.soc_code.*null"):
            backend.validate_spec_alignment(occupation_fixture(), df)

    def test_blank_soc_fails(self):
        df = occupation_fixture(); df.loc[0, "soc_code"] = "  "
        with self.assertRaisesRegex(backend.DataValidationError, "soc_code.*blank"):
            backend.validate_spec_alignment(df)

    def test_malformed_six_digit_soc_fails(self):
        df = occupation_fixture(); df.loc[0, "soc_code"] = "111011"
        with self.assertRaisesRegex(backend.DataValidationError, "Expected format"):
            backend.validate_spec_alignment(df)

    def test_malformed_onet_soc_fails(self):
        df = task_fixture(); df.loc[0, "onet_soc_code"] = "11-1011"
        with self.assertRaisesRegex(backend.DataValidationError, "onet_soc_code.*malformed"):
            backend.validate_spec_alignment(occupation_fixture(), df)

    def test_null_and_blank_onet_soc_fail(self):
        for value, failure in ((None, "null"), (" ", "blank")):
            with self.subTest(value=value):
                df = task_fixture(); df.loc[0, "onet_soc_code"] = value
                with self.assertRaisesRegex(backend.DataValidationError, f"onet_soc_code.*{failure}"):
                    backend.validate_spec_alignment(occupation_fixture(), df)

    def test_null_and_blank_task_ids_fail(self):
        for value, text in ((None, "null"), ("  ", "blank")):
            with self.subTest(value=value):
                df = task_fixture(); df.loc[0, "task_id"] = value
                with self.assertRaisesRegex(backend.DataValidationError, f"task_id.*{text}"):
                    backend.validate_spec_alignment(occupation_fixture(), df)

    def test_null_and_blank_task_text_fail(self):
        for column in ("task", "task_normalized"):
            for value in (None, " "):
                with self.subTest(column=column, value=value):
                    df = task_fixture(); df.loc[0, column] = value
                    with self.assertRaises(backend.DataValidationError):
                        backend.validate_spec_alignment(occupation_fixture(), df)

    def test_duplicate_onet_task_key_fails(self):
        across_detailed_codes = task_fixture(2)
        across_detailed_codes.loc[1, "onet_soc_code"] = "11-1011.03"
        across_detailed_codes.loc[1, "task_id"] = across_detailed_codes.loc[0, "task_id"]
        backend.validate_spec_alignment(occupation_fixture(), across_detailed_codes)
        df = task_fixture(2); df.loc[1, "task_id"] = df.loc[0, "task_id"]
        with self.assertRaisesRegex(backend.DataValidationError, "onet_soc_code, task_id"):
            backend.validate_spec_alignment(occupation_fixture(), df)

    def test_task_count_constraints(self):
        for mapped, positive, pct in ((-1, 0, 0), (1.5, 1, 2 / 3), (1, 2, 2), (2, 1, 0.4)):
            with self.subTest(mapped=mapped, positive=positive, pct=pct):
                df = occupation_fixture()
                df["mapped_task_count"] = df.mapped_task_count.astype(float)
                df["positive_penetration_task_count"] = df.positive_penetration_task_count.astype(float)
                df.loc[0, ["mapped_task_count", "positive_penetration_task_count", "positive_penetration_task_pct"]] = [mapped, positive, pct]
                with self.assertRaises(backend.DataValidationError):
                    backend.validate_spec_alignment(df)

    def test_zero_task_rule_counts_zero_percentage_missing(self):
        df = occupation_fixture()
        df.loc[0, ["mapped_task_count", "positive_penetration_task_count"]] = [0, 0]
        df.loc[0, "positive_penetration_task_pct"] = np.nan
        backend.validate_spec_alignment(df)
        df.loc[0, "positive_penetration_task_pct"] = 0
        with self.assertRaisesRegex(backend.DataValidationError, "zero-task rule"):
            backend.validate_spec_alignment(df)

    def test_invalid_numeric_strings_are_not_treated_as_missing(self):
        cases = (("occupation", "observed_exposure"), ("occupation", "mapped_task_count"),
                 ("occupation", "employment_base_year"), ("occupation", "employment_growth_pct"),
                 ("occupation", "annual_openings"), ("occupation", "median_annual_wage"),
                 ("task", "penetration"), ("task", "augmentation_share"))
        for frame_name, column in cases:
            with self.subTest(frame=frame_name, column=column):
                occ, tasks = occupation_fixture(), task_fixture()
                frame = occ if frame_name == "occupation" else tasks
                frame[column] = frame[column].astype(object)
                frame.loc[0, column] = "not-a-number"
                with self.assertRaisesRegex(backend.DataValidationError, f"{column}.*invalid numeric"):
                    backend.validate_spec_alignment(occ, tasks)

    def test_invalid_dataset_mode_fails(self):
        df = occupation_fixture(); df["dominant_mode"] = df.dominant_mode.astype(object); df.loc[0, "dominant_mode"] = "replacement"
        with self.assertRaisesRegex(backend.DataValidationError, "dominant_mode"):
            backend.validate_spec_alignment(df)


class FilterValidationTests(unittest.TestCase):
    def setUp(self):
        self.df = occupation_fixture()

    def assert_bad(self, **kwargs):
        with self.assertRaises(ValueError):
            backend.filter_occupations(self.df, **kwargs)

    def test_reversed_growth_range_fails(self): self.assert_bad(growth_range=(2, 1))
    def test_reversed_exposure_range_fails(self): self.assert_bad(exposure_range=(0.8, 0.2))
    def test_exposure_bounds_outside_unit_interval_fail(self):
        self.assert_bad(exposure_range=(-0.1, 0.2)); self.assert_bad(exposure_range=(0.2, 1.1))
    def test_negative_minimum_employment_fails(self): self.assert_bad(min_employment=-1)
    def test_nonfinite_filter_bounds_fail(self):
        self.assert_bad(growth_range=(np.nan, None)); self.assert_bad(exposure_range=(None, np.inf))
        self.assert_bad(min_employment=np.nan); self.assert_bad(min_employment=np.inf)
        self.assert_bad(growth_range=("1", None)); self.assert_bad(min_employment="10")

    def test_filter_ranges_require_exactly_two_bounds(self):
        self.assert_bad(growth_range=(1,)); self.assert_bad(exposure_range=(0, 0.5, 1))
    def test_unknown_dominant_mode_fails(self): self.assert_bad(dominant_modes=["replacement"])

    def test_partial_ranges_and_empty_modes_are_valid(self):
        result = backend.filter_occupations(self.df, growth_range=(None, 10), exposure_range=(0.1, None), dominant_modes=[])
        self.assertEqual(len(result), 1)

    def test_documented_mode_filter_returns_only_known_selected_modes(self):
        df = occupation_fixture(3)
        df["soc_code"] = ["11-1011", "11-1021", "11-1031"]
        df["dominant_mode"] = ["augmentation", "automation", np.nan]
        result = backend.filter_occupations(df, dominant_modes=["augmentation"])
        self.assertEqual(result.soc_code.tolist(), ["11-1011"])

    def test_mode_breakdown_reports_filtered_residual(self):
        df = occupation_fixture(2)
        df.loc[0, "augmentation_share"] = 0.3
        df.loc[0, "automation_share"] = 0.4
        df["dominant_mode"] = df.dominant_mode.astype(object)
        df.loc[0, "dominant_mode"] = "automation"
        result = backend.get_mode_breakdown(df)
        self.assertAlmostEqual(result.loc[0, "filtered_share"], 0.3)
        self.assertTrue(pd.isna(result.loc[1, "filtered_share"]))


class RankingCompatibilityTests(unittest.TestCase):
    def test_priority_scores_and_tied_rank_behavior(self):
        df = occupation_fixture(2)
        df.loc[1, "soc_code"] = "11-1021"
        df.loc[1, "occupation_title"] = "General Manager"
        scored = backend.add_priority_score(df)
        self.assertTrue(scored.priority_score.eq(scored.priority_score.iloc[0]).all())
        self.assertAlmostEqual(scored.priority_score.iloc[0], 75.0)
        ranked = backend.rank_occupations(df, top_n=None)
        self.assertEqual(ranked["rank"].tolist(), [1, 1])
        self.assertEqual(ranked.occupation_title.tolist(), ["Chief Executive", "General Manager"])

    def test_four_row_priority_score_matches_hand_calculation(self):
        df = occupation_fixture(4)
        df["soc_code"] = ["11-1011", "11-1021", "11-1031", "11-1041"]
        df["occupation_title"] = ["A", "B", "C", "D"]
        df["observed_exposure"] = [0.1, 0.2, 0.3, 0.4]
        df["employment_base_year"] = [100, 200, 300, 400]
        df["employment_growth_pct"] = [1, 2, 3, 4]
        df["annual_openings"] = [10, 20, 30, 40]
        ranked = backend.rank_occupations(df, top_n=None)
        expected_scores = {"A": 25.0, "B": 50.0, "C": 75.0, "D": 100.0}
        for title, score in expected_scores.items():
            row = ranked.set_index("occupation_title").loc[title]
            self.assertAlmostEqual(row.priority_score, score)
            self.assertEqual(int(row["rank"]), ord("D") - ord(title) + 1)
            contributions = [row[f"{part}_contribution"] for part in ("exposure", "employment", "growth", "openings")]
            self.assertAlmostEqual(sum(contributions), score)
        highest = ranked.set_index("occupation_title").loc["D"]
        for part, value in (("exposure", 45), ("employment", 25), ("growth", 15), ("openings", 15)):
            self.assertAlmostEqual(highest[f"{part}_contribution"], value)

    def test_top_n_requires_positive_integer(self):
        for value in (0, -1, 1.5, "2", True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                backend.rank_occupations(occupation_fixture(), top_n=value)

    def test_dashboard_outputs_keep_full_ranking_separate_from_visual(self):
        occupations = occupation_fixture(4)
        occupations["soc_code"] = ["11-1011", "11-1021", "11-1031", "11-1041"]
        occupations["occupation_title"] = ["A", "B", "C", "D"]
        tasks = task_fixture()
        with patch.object(backend, "load_occupation_data", return_value=occupations), \
             patch.object(backend, "load_task_data", return_value=tasks):
            outputs = backend.build_dashboard_outputs(top_n=2)
        self.assertEqual(len(outputs["ranking"]), 4)
        self.assertEqual(len(outputs["ranking_visual"]), 2)
        self.assertEqual(outputs["summary"]["occupations_analyzed"], 4)


if __name__ == "__main__":
    unittest.main()
