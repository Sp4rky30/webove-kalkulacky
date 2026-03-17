import unittest

from werkzeug.exceptions import BadRequest

from app import app
from calculators.family import (
    build_maternity_context,
    build_parental_context,
    build_sickness_context,
    get_parental_inputs,
)


class FamilyCalculatorTests(unittest.TestCase):
    def test_maternity_context_returns_expected_duration(self):
        context = build_maternity_context({"gross_salary": 45_000, "duration_type": "mother_single"})

        self.assertEqual(context["summary_cards"][3]["value"], "28 týdnů")
        self.assertEqual(context["breakdown_rows"][4]["value"], "196 dní")

    def test_parental_monthly_mode_respects_monthly_limit(self):
        context = build_parental_context(
            {
                "gross_salary": 45_000,
                "birth_period": "2026_plus",
                "multiple_children": False,
                "has_dvz": False,
                "calculation_mode": "monthly_amount",
                "desired_monthly_draw": 20_000,
                "desired_months": 24,
            }
        )

        self.assertEqual(context["summary_cards"][0]["value"], "350 000 Kč")
        self.assertEqual(context["summary_cards"][1]["value"], "15 000 Kč")
        self.assertEqual(context["summary_cards"][2]["value"], "15 000 Kč")
        self.assertEqual(context["summary_cards"][3]["value"], "24 měsíců")

    def test_parental_duration_mode_computes_monthly_draw(self):
        context = build_parental_context(
            {
                "gross_salary": 45_000,
                "birth_period": "2026_plus",
                "multiple_children": False,
                "has_dvz": True,
                "calculation_mode": "duration_months",
                "desired_monthly_draw": 15_000,
                "desired_months": 30,
            }
        )

        self.assertEqual(context["summary_cards"][2]["value"], "11 667 Kč")
        self.assertEqual(context["summary_cards"][3]["value"], "30 měsíců")

    def test_sickness_context_splits_periods_correctly(self):
        context = build_sickness_context({"gross_salary": 45_000, "sick_days": 65})

        self.assertEqual(len(context["period_rows"]), 3)
        self.assertEqual(context["period_rows"][0]["days"], 16)
        self.assertEqual(context["period_rows"][1]["days"], 30)
        self.assertEqual(context["period_rows"][2]["days"], 5)

    def test_parental_validates_active_mode_inputs_only(self):
        with app.test_request_context(
            "/kalkulacky/rodicovska",
            method="POST",
            data={
                "gross_salary": "45000",
                "birth_period": "2026_plus",
                "calculation_mode": "duration_months",
                "desired_monthly_draw": "0",
                "desired_months": "30",
            },
        ):
            from flask import request

            inputs = get_parental_inputs(request)

        self.assertEqual(inputs["desired_months"], 30)

    def test_parental_rejects_zero_duration_in_duration_mode(self):
        with app.test_request_context(
            "/kalkulacky/rodicovska",
            method="POST",
            data={
                "gross_salary": "45000",
                "birth_period": "2026_plus",
                "calculation_mode": "duration_months",
                "desired_monthly_draw": "0",
                "desired_months": "0",
            },
        ):
            from flask import request

            with self.assertRaises(BadRequest) as ctx:
                get_parental_inputs(request)

        self.assertIn("Požadovaná délka čerpání", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
