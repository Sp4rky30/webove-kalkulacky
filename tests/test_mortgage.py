import unittest

from werkzeug.exceptions import BadRequest

from app import app
from calculators.mortgage import calculate_mortgage_schedule, get_mortgage_inputs


class MortgageCalculatorTests(unittest.TestCase):
    def test_zero_interest_schedule_has_no_interest(self):
        schedule = calculate_mortgage_schedule(loan_amount=1_200_000, annual_rate=0, years=10)

        self.assertEqual(schedule["monthly_payment"], 10_000.0)
        self.assertEqual(schedule["total_interest"], 0.0)
        self.assertEqual(schedule["total_paid"], 1_200_000.0)
        self.assertEqual(schedule["actual_months"], 120)
        self.assertEqual(len(schedule["chart_labels"]), 10)

    def test_own_resources_cannot_exceed_property_price(self):
        with app.test_request_context(
            "/kalkulacky/hypoteka",
            method="POST",
            data={"property_price": "5000000", "own_resources": "6000000", "interest_rate": "4.5", "years": "30"},
        ):
            from flask import request

            with self.assertRaises(BadRequest) as ctx:
                get_mortgage_inputs(request)

        self.assertIn("Vlastní zdroje", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
