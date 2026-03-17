import unittest

from flask import request
from werkzeug.exceptions import BadRequest

from app import app
from calculators.net_salary import build_net_salary_context, get_net_salary_inputs


class NetSalaryCalculatorTests(unittest.TestCase):
    def test_employment_with_taxpayer_credit_returns_expected_net_salary(self):
        inputs = {
            "gross_salary": 45_000,
            "employment_type": "employment",
            "signed_tax_declaration": True,
            "taxpayer_ztp": False,
            "student": False,
            "invalidity_level": "none",
            "health_exemption_reason": "none",
            "children": [],
        }

        context = build_net_salary_context(inputs)

        self.assertEqual(context["net_salary_result"]["net_salary"], "35 600 Kč")
        self.assertEqual(context["net_salary_result"]["social_insurance"], "3 195 Kč")
        self.assertEqual(context["net_salary_result"]["health_insurance"], "2 025 Kč")
        self.assertEqual(context["net_salary_result"]["final_tax"], "4 180 Kč")

    def test_dpp_under_limit_does_not_pay_insurance(self):
        inputs = {
            "gross_salary": 10_000,
            "employment_type": "dpp",
            "signed_tax_declaration": False,
            "taxpayer_ztp": False,
            "student": False,
            "invalidity_level": "none",
            "health_exemption_reason": "none",
            "children": [],
        }

        context = build_net_salary_context(inputs)

        self.assertEqual(context["net_salary_result"]["net_salary"], "8 500 Kč")
        self.assertEqual(context["net_salary_result"]["social_insurance"], "0 Kč")
        self.assertEqual(context["net_salary_result"]["health_insurance"], "0 Kč")

    def test_invalid_child_type_raises_bad_request(self):
        with app.test_request_context(
            "/kalkulacky/cista-mzda",
            method="POST",
            data={"gross_salary": "45000", "child_type": ["normal", "hack"]},
        ):
            with self.assertRaises(BadRequest) as ctx:
                get_net_salary_inputs(request)

        self.assertIn("Děti pro daňové zvýhodnění", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
