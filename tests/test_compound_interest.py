import unittest
from unittest.mock import patch

from flask import request
from werkzeug.exceptions import BadRequest

from app import app
from calculators.compound_interest import (
    build_compound_context,
    calculate_compound_data,
    get_compound_inputs,
)


class CompoundInterestCalculatorTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_calculate_compound_data_without_interest_matches_deposits(self):
        data = calculate_compound_data(
            initial_deposit=100_000,
            annual_rate=0,
            monthly_deposit=5_000,
            years=2,
            inflation_rate=0,
        )

        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]["total"], 100_000)
        self.assertEqual(data[1]["deposits"], 160_000)
        self.assertEqual(data[1]["total"], 160_000)
        self.assertEqual(data[2]["deposits"], 220_000)
        self.assertEqual(data[2]["profit"], 0)
        self.assertEqual(data[2]["real_total"], 220_000)

    def test_build_compound_context_contains_expected_summary_and_milestones(self):
        context = build_compound_context(
            {
                "initial_deposit": 100_000,
                "annual_rate": 0,
                "monthly_deposit": 5_000,
                "inflation_rate": 0,
                "years": 6,
            }
        )

        self.assertEqual(context["summary"]["deposits"], "460 000 Kč")
        self.assertEqual(context["summary"]["total"], "460 000 Kč")
        self.assertEqual(context["summary"]["profit"], "0 Kč")
        self.assertEqual([item["year"] for item in context["milestones"]], [5, 6])
        self.assertEqual(context["chart_labels"], [0, 1, 2, 3, 4, 5, 6])

    def test_get_compound_inputs_rejects_invalid_values(self):
        with app.test_request_context(
            "/kalkulacky/slozene-uroceni",
            method="POST",
            data={
                "initial_deposit": "100000",
                "annual_rate": "7",
                "monthly_deposit": "2000000",
                "inflation_rate": "2.5",
                "years": "40",
            },
        ):
            with self.assertRaises(BadRequest) as ctx:
                get_compound_inputs(request)

        self.assertIn("Měsíční vklad", str(ctx.exception))

    def test_csv_export_route_returns_attachment(self):
        response = self.client.get(
            "/kalkulacky/slozene-uroceni/export/csv"
            "?initial_deposit=100000&annual_rate=0&monthly_deposit=5000&inflation_rate=0&years=2"
        )

        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("attachment; filename=slozene-uroceni.csv", response.headers["Content-Disposition"])
        self.assertIn("Rok;Celkem vlozeno;Celkova hodnota;Zisk;Realna hodnota", body)
        self.assertIn("2;220000.00;220000.00;0.00;220000.00", body)

    def test_pdf_export_route_returns_pdf_attachment(self):
        with patch("calculators.compound_exports.register_pdf_font", return_value="Helvetica"):
            response = self.client.get(
                "/kalkulacky/slozene-uroceni/export/pdf"
                "?initial_deposit=100000&annual_rate=0&monthly_deposit=5000&inflation_rate=0&years=2"
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        self.assertIn("attachment; filename=slozene-uroceni.pdf", response.headers["Content-Disposition"])
        self.assertTrue(response.get_data().startswith(b"%PDF"))

    def test_pdf_export_invalid_input_returns_localized_error(self):
        response = self.client.get(
            "/kalkulacky/slozene-uroceni/export/pdf"
            "?initial_deposit=100000&annual_rate=101&monthly_deposit=5000&inflation_rate=0&years=2"
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Roční úrok", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
