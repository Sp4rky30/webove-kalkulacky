from .formatting import format_czk, format_percent
from .validation import parse_float, parse_int, validate_less_or_equal


def get_mortgage_inputs(req):
    property_price = parse_float(req, "property_price", 6_500_000, "Cena nemovitosti", min_value=0, max_value=100_000_000)
    own_resources = parse_float(req, "own_resources", 1_500_000, "Vlastní zdroje", min_value=0, max_value=100_000_000)
    interest_rate = parse_float(req, "interest_rate", 4.9, "Roční úrok", min_value=0, max_value=100)
    years = parse_int(req, "years", 30, "Doba splácení", min_value=1, max_value=40)
    validate_less_or_equal(own_resources, property_price, "Vlastní zdroje", "Cena nemovitosti")
    return {
        "property_price": property_price,
        "own_resources": own_resources,
        "interest_rate": interest_rate,
        "years": years,
    }


def calculate_mortgage_schedule(loan_amount, annual_rate, years):
    months = years * 12
    monthly_rate = annual_rate / 100 / 12
    if loan_amount <= 0:
        return {
            "monthly_payment": 0.0,
            "actual_months": 0,
            "total_interest": 0.0,
            "total_paid": 0.0,
            "milestones": [],
            "chart_labels": [],
            "chart_balances": [],
            "chart_interest_paid": [],
        }

    if monthly_rate == 0:
        base_payment = loan_amount / months
    else:
        base_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** months) / (((1 + monthly_rate) ** months) - 1)

    balance = loan_amount
    total_interest = 0.0
    total_paid = 0.0
    milestones = []
    milestone_months = {12, 60, 120, 180, 240, 300, 360, months}
    chart_labels = []
    chart_balances = []
    chart_interest_paid = []

    for month in range(1, months + 1):
        interest_part = balance * monthly_rate if monthly_rate else 0.0
        principal_part = base_payment - interest_part if monthly_rate else base_payment
        total_principal_payment = min(principal_part, balance)
        payment_this_month = interest_part + total_principal_payment
        balance = max(0.0, balance - total_principal_payment)
        total_interest += interest_part
        total_paid += payment_this_month

        if month % 12 == 0 or balance == 0:
            chart_labels.append(month // 12 if month % 12 == 0 else round(month / 12, 1))
            chart_balances.append(round(balance, 2))
            chart_interest_paid.append(round(total_interest, 2))

        if month in milestone_months or balance == 0:
            milestones.append(
                {
                    "month": month,
                    "year_label": f"{month / 12:.1f}".replace(".", ","),
                    "remaining_balance": round(balance, 2),
                    "paid_total": round(total_paid, 2),
                    "interest_total": round(total_interest, 2),
                }
            )

        if balance <= 0:
            return {
                "monthly_payment": round(base_payment, 2),
                "actual_months": month,
                "total_interest": round(total_interest, 2),
                "total_paid": round(total_paid, 2),
                "milestones": milestones,
                "chart_labels": chart_labels,
                "chart_balances": chart_balances,
                "chart_interest_paid": chart_interest_paid,
            }

    return {
        "monthly_payment": round(base_payment, 2),
        "actual_months": months,
        "total_interest": round(total_interest, 2),
        "total_paid": round(total_paid, 2),
        "milestones": milestones,
        "chart_labels": chart_labels,
        "chart_balances": chart_balances,
        "chart_interest_paid": chart_interest_paid,
    }


def build_mortgage_context(inputs):
    property_price = inputs["property_price"]
    own_resources = inputs["own_resources"]
    interest_rate = inputs["interest_rate"]
    years = inputs["years"]
    loan_amount = max(0.0, property_price - own_resources)
    ltv = (loan_amount / property_price * 100) if property_price else 0.0
    schedule = calculate_mortgage_schedule(loan_amount=loan_amount, annual_rate=interest_rate, years=years)
    actual_years = schedule["actual_months"] / 12 if schedule["actual_months"] else 0

    return {
        **inputs,
        "mortgage_result": {
            "loan_amount": format_czk(loan_amount),
            "monthly_payment": format_czk(schedule["monthly_payment"]),
            "total_interest": format_czk(schedule["total_interest"]),
            "total_paid": format_czk(schedule["total_paid"]),
            "ltv": format_percent(ltv),
            "actual_years": f"{actual_years:.1f}".replace(".", ","),
            "interest_rate": format_percent(interest_rate),
        },
        "summary_cards": [
            {"label": "Výše hypotéky", "value": format_czk(loan_amount)},
            {"label": "Měsíční splátka", "value": format_czk(schedule["monthly_payment"])},
            {"label": "Celkem zaplaceno", "value": format_czk(schedule["total_paid"])},
            {"label": "Celkový úrok", "value": format_czk(schedule["total_interest"])},
        ],
        "breakdown_rows": [
            {"label": "Cena nemovitosti", "value": format_czk(property_price)},
            {"label": "Vlastní zdroje", "value": format_czk(own_resources)},
            {"label": "Výše úvěru", "value": format_czk(loan_amount)},
            {"label": "LTV", "value": format_percent(ltv)},
            {"label": "Úroková sazba", "value": format_percent(interest_rate)},
            {"label": "Doba splácení", "value": f"{years} let"},
        ],
        "milestone_rows": [
            {
                "label": f"{item['year_label']} roku",
                "remaining_balance": format_czk(item["remaining_balance"]),
                "paid_total": format_czk(item["paid_total"]),
                "interest_total": format_czk(item["interest_total"]),
            }
            for item in schedule["milestones"]
        ],
        "chart_labels": schedule["chart_labels"],
        "chart_balances": schedule["chart_balances"],
        "chart_interest_paid": schedule["chart_interest_paid"],
        "notes": ["Vlastní zdroje pokrývají celou cenu nemovitosti, takže hypotéka není potřeba."] if loan_amount == 0 else [],
    }
