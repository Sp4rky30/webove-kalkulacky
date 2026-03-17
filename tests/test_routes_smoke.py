import unittest
from unittest.mock import patch

from app import app


class RouteSmokeTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_public_pages_render_successfully(self):
        routes = [
            "/",
            "/o-projektu",
            "/kalkulacky/slozene-uroceni",
            "/kalkulacky/cista-mzda",
            "/kalkulacky/hypoteka",
            "/kalkulacky/materska",
            "/kalkulacky/rodicovska",
            "/kalkulacky/nemocenska",
        ]

        for route in routes:
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 200)

    def test_health_endpoint_returns_ok_status(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})

    def test_google_analytics_script_is_rendered_when_measurement_id_is_set(self):
        with patch.dict("os.environ", {"GOOGLE_ANALYTICS_ID": "G-TEST123456"}, clear=False):
            response = self.client.get("/")

        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("googletagmanager.com/gtag/js?id=G-TEST123456", html)
        self.assertIn('gtag("config", "G-TEST123456")', html)

    def test_calculator_posts_render_successfully_with_defaults(self):
        routes_with_payloads = {
            "/kalkulacky/slozene-uroceni": {
                "initial_deposit": "100000",
                "annual_rate": "7",
                "monthly_deposit": "5000",
                "inflation_rate": "2.5",
                "years": "40",
            },
            "/kalkulacky/cista-mzda": {
                "gross_salary": "45000",
                "employment_type": "employment",
                "invalidity_level": "none",
                "health_exemption_reason": "none",
                "signed_tax_declaration": "on",
            },
            "/kalkulacky/hypoteka": {
                "property_price": "6500000",
                "own_resources": "1500000",
                "interest_rate": "4.9",
                "years": "30",
            },
            "/kalkulacky/materska": {
                "gross_salary": "45000",
                "duration_type": "mother_single",
            },
            "/kalkulacky/rodicovska": {
                "gross_salary": "45000",
                "birth_period": "2026_plus",
                "calculation_mode": "monthly_amount",
                "desired_monthly_draw": "15000",
                "desired_months": "24",
                "has_dvz": "on",
            },
            "/kalkulacky/nemocenska": {
                "gross_salary": "45000",
                "sick_days": "30",
            },
        }

        for route, payload in routes_with_payloads.items():
            with self.subTest(route=route):
                response = self.client.post(route, data=payload)
                self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
