import math

from werkzeug.exceptions import BadRequest

from .formatting import format_czk, format_number
from .validation import parse_choice, parse_float, parse_int

MATERNITY_DURATION_OPTIONS = (
    ("mother_single", "Matka - jedno dítě (28 týdnů)"),
    ("mother_multiple", "Matka - dvojčata a více dětí (37 týdnů)"),
    ("caregiver_single", "Jiný pojištěnec - jedno dítě (22 týdnů)"),
    ("caregiver_multiple", "Jiný pojištěnec - dvě a více dětí (31 týdnů)"),
)
PARENTAL_BIRTH_PERIOD_OPTIONS = (
    ("before_2024", "Dítě narozené do 31. 12. 2023"),
    ("2024_2025", "Dítě narozené od 1. 1. 2024 do 31. 12. 2025"),
    ("2026_plus", "Dítě narozené od 1. 1. 2026"),
)


def estimate_daily_base_from_monthly_salary(monthly_salary: float) -> float:
    return monthly_salary * 12 / 365 if monthly_salary > 0 else 0.0


def reduce_dvz_for_maternity(dvz: float) -> float:
    if dvz <= 0:
        return 0.0
    first = min(dvz, 1633)
    second = min(max(dvz - 1633, 0), 2449 - 1633)
    third = min(max(dvz - 2449, 0), 4897 - 2449)
    return first + second * 0.6 + third * 0.3


def reduce_dvz_for_sickness(dvz: float) -> float:
    if dvz <= 0:
        return 0.0
    first = min(dvz, 1633)
    second = min(max(dvz - 1633, 0), 2449 - 1633)
    third = min(max(dvz - 2449, 0), 4897 - 2449)
    return first * 0.9 + second * 0.6 + third * 0.3


def get_maternity_inputs(req):
    gross_salary = parse_float(req, "gross_salary", 45_000, "Hrubá mzda", min_value=0, max_value=1_000_000)
    duration_type = parse_choice(req, "duration_type", "mother_single", {option[0] for option in MATERNITY_DURATION_OPTIONS}, "Typ pobírání PPM")
    return {"gross_salary": gross_salary, "duration_type": duration_type}


def build_maternity_context(inputs):
    weeks_by_type = {
        "mother_single": 28,
        "mother_multiple": 37,
        "caregiver_single": 22,
        "caregiver_multiple": 31,
    }
    weeks = weeks_by_type[inputs["duration_type"]]
    dvz = estimate_daily_base_from_monthly_salary(inputs["gross_salary"])
    reduced_dvz = reduce_dvz_for_maternity(dvz)
    daily_benefit = reduced_dvz * 0.7
    total_days = weeks * 7
    total_benefit = daily_benefit * total_days
    approx_monthly = daily_benefit * 30
    return {
        **inputs,
        "duration_options": MATERNITY_DURATION_OPTIONS,
        "summary_cards": [
            {"label": "Orientační měsíční PPM", "value": format_czk(approx_monthly)},
            {"label": "Denní dávka", "value": format_czk(daily_benefit)},
            {"label": "Celkem za celé období", "value": format_czk(total_benefit)},
            {"label": "Délka pobírání", "value": f"{weeks} týdnů"},
        ],
        "breakdown_rows": [
            {"label": "Hrubá měsíční mzda", "value": format_czk(inputs["gross_salary"])},
            {"label": "Odhad denního vyměřovacího základu", "value": f"{format_number(dvz)} Kč"},
            {"label": "Redukovaný DVZ", "value": f"{format_number(reduced_dvz)} Kč"},
            {"label": "Denní PPM (70 %)", "value": f"{format_number(daily_benefit)} Kč"},
            {"label": "Počet kalendářních dnů", "value": f"{total_days} dní"},
        ],
        "notes": [
            "Výpočet je orientační a vychází z běžného zaměstnání s pravidelnou hrubou mzdou.",
            "PPM se v praxi počítá z denního vyměřovacího základu z rozhodného období, ne jen z jedné měsíční mzdy.",
        ],
    }


def get_parental_inputs(req):
    gross_salary = parse_float(req, "gross_salary", 45_000, "Hrubá mzda pro odhad DVZ", min_value=0, max_value=1_000_000)
    birth_period = parse_choice(req, "birth_period", "2026_plus", {option[0] for option in PARENTAL_BIRTH_PERIOD_OPTIONS}, "Období narození dítěte")
    calculation_mode = parse_choice(req, "calculation_mode", "monthly_amount", {"monthly_amount", "duration_months"}, "Způsob výpočtu")
    desired_monthly_draw = parse_float(req, "desired_monthly_draw", 15_000, "Požadovaná měsíční částka", min_value=0, max_value=700_000)
    desired_months = parse_int(req, "desired_months", 24, "Požadovaná délka čerpání", min_value=0, max_value=120)

    if calculation_mode == "monthly_amount" and desired_monthly_draw <= 0:
        raise BadRequest("Pole 'Požadovaná měsíční částka' musí být alespoň 1.")
    if calculation_mode == "duration_months" and desired_months < 1:
        raise BadRequest("Pole 'Požadovaná délka čerpání' musí být alespoň 1.")

    return {
        "gross_salary": gross_salary,
        "birth_period": birth_period,
        "multiple_children": req.values.get("multiple_children") == "on",
        "has_dvz": req.values.get("has_dvz") != "off",
        "calculation_mode": calculation_mode,
        "desired_monthly_draw": desired_monthly_draw,
        "desired_months": desired_months,
    }


def build_parental_context(inputs):
    total_amount_map = {
        "before_2024": 450_000 if inputs["multiple_children"] else 300_000,
        "2024_2025": 525_000 if inputs["multiple_children"] else 350_000,
        "2026_plus": 700_000 if inputs["multiple_children"] else 350_000,
    }
    total_amount = total_amount_map[inputs["birth_period"]]
    dvz = estimate_daily_base_from_monthly_salary(inputs["gross_salary"])
    monthly_limit_from_dvz = dvz * 0.7 * 30
    if inputs["has_dvz"]:
        monthly_limit = max(30_000, monthly_limit_from_dvz * 2) if inputs["multiple_children"] else max(15_000, monthly_limit_from_dvz)
    else:
        monthly_limit = 30_000 if inputs["multiple_children"] else 15_000

    if inputs["calculation_mode"] == "duration_months":
        effective_monthly_draw = math.ceil(total_amount / inputs["desired_months"]) if inputs["desired_months"] > 0 else total_amount
    else:
        effective_monthly_draw = inputs["desired_monthly_draw"] if inputs["desired_monthly_draw"] > 0 else monthly_limit
    effective_monthly_draw = min(effective_monthly_draw, monthly_limit, total_amount)
    duration_months = math.ceil(total_amount / effective_monthly_draw) if effective_monthly_draw > 0 else 0

    notes = [
        "Rodičovský příspěvek si můžeš průběžně měnit, pokud je možné doložit DVZ.",
        "Výpočet ukazuje maximální měsíční limit a orientační délku čerpání při zvolené částce.",
    ]
    if not inputs["has_dvz"]:
        notes.append("Pokud nelze určit denní vyměřovací základ, použije se jen zákonný měsíční strop bez návaznosti na mzdu.")

    return {
        **inputs,
        "birth_period_options": PARENTAL_BIRTH_PERIOD_OPTIONS,
        "summary_cards": [
            {"label": "Celkový rodičovský příspěvek", "value": format_czk(total_amount)},
            {"label": "Maximální měsíční čerpání", "value": format_czk(monthly_limit)},
            {"label": "Zvolená měsíční částka", "value": format_czk(effective_monthly_draw)},
            {"label": "Orientační délka čerpání", "value": f"{duration_months} měsíců"},
        ],
        "breakdown_rows": [
            {"label": "Období narození dítěte", "value": dict(PARENTAL_BIRTH_PERIOD_OPTIONS)[inputs["birth_period"]]},
            {"label": "Počet dětí při narození", "value": "Více dětí" if inputs["multiple_children"] else "Jedno dítě"},
            {"label": "Lze stanovit DVZ", "value": "Ano" if inputs["has_dvz"] else "Ne"},
            {"label": "Odhadovaný DVZ", "value": f"{format_number(dvz)} Kč"},
            {"label": "Limit podle DVZ", "value": format_czk(monthly_limit_from_dvz if not inputs["multiple_children"] else monthly_limit_from_dvz * 2)},
            {"label": "Režim výpočtu", "value": "Podle měsíční částky" if inputs["calculation_mode"] == "monthly_amount" else "Podle délky čerpání"},
        ],
        "notes": notes,
    }


def get_sickness_inputs(req):
    return {
        "gross_salary": parse_float(req, "gross_salary", 45_000, "Hrubá mzda", min_value=0, max_value=1_000_000),
        "sick_days": parse_int(req, "sick_days", 30, "Počet dní neschopenky", min_value=15, max_value=365),
    }


def build_sickness_context(inputs):
    dvz = estimate_daily_base_from_monthly_salary(inputs["gross_salary"])
    reduced_dvz = reduce_dvz_for_sickness(dvz)
    periods = []
    total_sickness = 0.0
    if inputs["sick_days"] >= 15:
        for start, end, rate, label in [
            (15, min(inputs["sick_days"], 30), 0.6, "15.-30. den"),
            (31, min(inputs["sick_days"], 60), 0.66, "31.-60. den"),
            (61, inputs["sick_days"], 0.72, "61. den a dál"),
        ]:
            if end >= start:
                days = end - start + 1
                amount = reduced_dvz * rate * days
                total_sickness += amount
                periods.append({"label": label, "days": days, "rate": f"{rate * 100:.1f} %".replace(".", ","), "value": format_czk(amount)})

    return {
        **inputs,
        "summary_cards": [
            {"label": "Celkem nemocenská", "value": format_czk(total_sickness)},
            {"label": "Odhad DVZ", "value": f"{format_number(dvz)} Kč"},
            {"label": "Redukovaný DVZ", "value": f"{format_number(reduced_dvz)} Kč"},
            {"label": "Orientační měsíční nemocenská", "value": format_czk(reduced_dvz * 0.6 * 30)},
        ],
        "breakdown_rows": [
            {"label": "Hrubá měsíční mzda", "value": format_czk(inputs["gross_salary"])},
            {"label": "Délka neschopenky", "value": f"{inputs['sick_days']} dní"},
            {"label": "Denní vyměřovací základ", "value": f"{format_number(dvz)} Kč"},
            {"label": "Redukovaný DVZ", "value": f"{format_number(reduced_dvz)} Kč"},
        ],
        "period_rows": periods,
        "notes": [
            "Kalkulačka počítá nemocenskou od 15. kalendářního dne pracovní neschopnosti.",
            "Náhradu mzdy od zaměstnavatele za prvních 14 dní nepočítá, protože závisí i na rozvrhu směn a průměrném hodinovém výdělku.",
        ],
    }
