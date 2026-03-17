from .formatting import format_czk
from .validation import parse_float, parse_int


def calculate_compound_data(
    initial_deposit: float,
    annual_rate: float,
    monthly_deposit: float,
    years: int,
    inflation_rate: float,
):
    monthly_rate = annual_rate / 100 / 12
    monthly_inflation_rate = inflation_rate / 100 / 12

    total_value = initial_deposit
    total_deposits = initial_deposit

    data = [
        {
            "year": 0,
            "deposits": round(total_deposits, 2),
            "total": round(total_value, 2),
            "profit": round(total_value - total_deposits, 2),
            "real_total": round(total_value, 2),
        }
    ]

    for month in range(1, years * 12 + 1):
        total_value = total_value * (1 + monthly_rate) + monthly_deposit
        total_deposits += monthly_deposit

        if month % 12 == 0:
            year = month // 12
            inflation_factor = (1 + monthly_inflation_rate) ** month
            real_total = total_value / inflation_factor if inflation_factor > 0 else total_value
            data.append(
                {
                    "year": year,
                    "deposits": round(total_deposits, 2),
                    "total": round(total_value, 2),
                    "profit": round(total_value - total_deposits, 2),
                    "real_total": round(real_total, 2),
                }
            )

    return data


def get_compound_inputs(req):
    initial_deposit = parse_float(req, "initial_deposit", 100000, "Začáteční vklad", min_value=0, max_value=100_000_000)
    annual_rate = parse_float(req, "annual_rate", 7, "Roční úrok", min_value=0, max_value=100)
    monthly_deposit = parse_float(req, "monthly_deposit", 5000, "Měsíční vklad", min_value=0, max_value=1_000_000)
    inflation_rate = parse_float(req, "inflation_rate", 2.5, "Inflace", min_value=0, max_value=100)
    years = parse_int(req, "years", 40, "Počet let", min_value=1, max_value=100)

    return {
        "initial_deposit": initial_deposit,
        "annual_rate": annual_rate,
        "monthly_deposit": monthly_deposit,
        "inflation_rate": inflation_rate,
        "years": years,
    }


def build_compound_context(inputs):
    data = calculate_compound_data(
        initial_deposit=inputs["initial_deposit"],
        annual_rate=inputs["annual_rate"],
        monthly_deposit=inputs["monthly_deposit"],
        years=inputs["years"],
        inflation_rate=inputs["inflation_rate"],
    )

    milestone_years = set(range(5, inputs["years"] + 1, 5))
    milestone_years.add(inputs["years"])
    milestones = [
        {
            "year": row["year"],
            "deposits": format_czk(row["deposits"]),
            "total": format_czk(row["total"]),
            "profit": format_czk(row["profit"]),
            "real_total": format_czk(row["real_total"]),
        }
        for row in data
        if row["year"] in milestone_years
    ]

    final_row = data[-1]
    summary = {
        "deposits": format_czk(final_row["deposits"]),
        "total": format_czk(final_row["total"]),
        "profit": format_czk(final_row["profit"]),
        "real_total": format_czk(final_row["real_total"]),
    }

    return {
        **inputs,
        "milestones": milestones,
        "summary": summary,
        "chart_labels": [row["year"] for row in data],
        "chart_deposits": [row["deposits"] for row in data],
        "chart_total": [row["total"] for row in data],
        "chart_profit": [row["profit"] for row in data],
        "chart_real_total": [row["real_total"] for row in data],
    }
