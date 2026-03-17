import unittest

from app import app


class AppErrorHandlingTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_invalid_compound_input_returns_localized_error_page(self):
        response = self.client.post(
            "/kalkulacky/slozene-uroceni",
            data={"initial_deposit": "-1", "annual_rate": "7", "monthly_deposit": "5000", "inflation_rate": "2.5", "years": "40"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Neplatný vstup", response.get_data(as_text=True))
        self.assertIn("Začáteční vklad", response.get_data(as_text=True))

    def test_not_found_uses_shared_error_page(self):
        response = self.client.get("/neexistuje")

        self.assertEqual(response.status_code, 404)
        self.assertIn("Stránka nenalezena", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
