import math

from .formatting import format_czk, format_percent
from .validation import parse_choice, parse_choice_list, parse_float

AVG_WAGE_2026 = 48_967
MIN_WAGE_2026 = 22_400
SOCIAL_INSURANCE_RATE = 0.071
HEALTH_INSURANCE_EMPLOYEE_RATE = 0.045
HEALTH_INSURANCE_TOTAL_RATE = 0.135
HIGHER_TAX_THRESHOLD_MONTHLY = AVG_WAGE_2026 * 4
MONTHLY_TAXPAYER_CREDIT = 2_570
MONTHLY_INVALIDITY_1_2_CREDIT = 210
MONTHLY_INVALIDITY_3_CREDIT = 420
MONTHLY_ZTP_CREDIT = 1_345
MONTHLY_CHILD_BENEFITS = (1_267, 1_860, 2_320)
MONTHLY_BONUS_INCOME_LIMIT = 11_200
EMPLOYMENT_TYPE_OPTIONS = (
    ("employment", "Pracovní poměr (HPP)"),
    ("dpc", "Dohoda o pracovní činnosti (DPČ)"),
    ("dpp", "Dohoda o provedení práce (DPP)"),
)
HEALTH_EXEMPTION_OPTIONS = (
    ("none", "Ne"),
    ("student", "Student / soustavná příprava"),
    ("pensioner", "Důchodce"),
    ("parental", "Rodičovská / mateřská"),
    ("jobseeker", "Evidence na ÚP"),
    ("other_state", "Jiný státní pojištěnec"),
)


def get_child_entries(req):
    entries = []
    child_types = parse_choice_list(req, "child_type", {"normal", "ztp"}, "Děti pro daňové zvýhodnění", max_items=10)
    for index, child_type in enumerate(child_types, start=1):
        entries.append(
            {
                "label": f"Dítě {index}",
                "type": child_type,
                "ztp": child_type == "ztp",
            }
        )
    return entries


def round_tax_base(value: float) -> int:
    if value <= 100:
        return math.ceil(value)
    return int(math.ceil(value / 100.0) * 100)


def calculate_advance_tax(tax_base: int) -> int:
    lower_part = min(tax_base, HIGHER_TAX_THRESHOLD_MONTHLY)
    higher_part = max(0, tax_base - HIGHER_TAX_THRESHOLD_MONTHLY)
    return math.ceil(lower_part * 0.15 + higher_part * 0.23)


def calculate_child_tax_credit(children):
    total = 0
    detail = []
    for index, child in enumerate(children, start=1):
        base_amount = MONTHLY_CHILD_BENEFITS[min(index - 1, 2)]
        amount = base_amount * (2 if child["ztp"] else 1)
        detail.append({"label": child["label"], "amount": amount, "ztp": child["ztp"]})
        total += amount
    return total, detail


def get_net_salary_inputs(req):
    gross_salary = parse_float(req, "gross_salary", 45_000, "Hrubá mzda", min_value=0, max_value=1_000_000)
    employment_type = parse_choice(req, "employment_type", "employment", {option[0] for option in EMPLOYMENT_TYPE_OPTIONS}, "Typ pracovního vztahu")
    invalidity_level = parse_choice(req, "invalidity_level", "none", {"none", "1_2", "3"}, "Invalidita")
    health_exemption_reason = parse_choice(req, "health_exemption_reason", "none", {option[0] for option in HEALTH_EXEMPTION_OPTIONS}, "Výjimka z minima zdravotního pojištění")

    return {
        "gross_salary": gross_salary,
        "employment_type": employment_type,
        "signed_tax_declaration": req.values.get("signed_tax_declaration") == "on",
        "taxpayer_ztp": req.values.get("taxpayer_ztp") == "on",
        "student": req.values.get("student") == "on",
        "invalidity_level": invalidity_level,
        "health_exemption_reason": health_exemption_reason,
        "children": get_child_entries(req),
    }


def build_net_salary_context(inputs):
    gross_salary = inputs["gross_salary"]
    employment_type = inputs["employment_type"]
    signed_tax_declaration = inputs["signed_tax_declaration"]
    taxpayer_ztp = inputs["taxpayer_ztp"]
    invalidity_level = inputs["invalidity_level"]
    health_exemption_reason = inputs["health_exemption_reason"]
    children = inputs["children"]

    participates_social = employment_type == "employment" or (
        employment_type == "dpc" and gross_salary >= 4_500
    ) or (
        employment_type == "dpp" and gross_salary >= 12_000
    )
    participates_health = participates_social
    minimum_health_applies = (
        employment_type == "employment"
        and participates_health
        and health_exemption_reason == "none"
        and gross_salary < MIN_WAGE_2026
    )

    social_insurance = math.ceil(gross_salary * SOCIAL_INSURANCE_RATE) if participates_social else 0
    health_insurance = 0
    health_minimum_top_up = 0
    if participates_health:
        health_insurance = math.ceil(gross_salary * HEALTH_INSURANCE_EMPLOYEE_RATE)
        if minimum_health_applies:
            health_minimum_top_up = math.ceil((MIN_WAGE_2026 - gross_salary) * HEALTH_INSURANCE_TOTAL_RATE)
            health_insurance += health_minimum_top_up

    tax_base = round_tax_base(gross_salary)
    pre_credit_tax = calculate_advance_tax(tax_base)

    taxpayer_credits = 0
    credit_items = []
    if signed_tax_declaration:
        taxpayer_credits += MONTHLY_TAXPAYER_CREDIT
        credit_items.append(("Sleva na poplatníka", MONTHLY_TAXPAYER_CREDIT))
        if invalidity_level == "1_2":
            taxpayer_credits += MONTHLY_INVALIDITY_1_2_CREDIT
            credit_items.append(("Invalidita I./II. stupně", MONTHLY_INVALIDITY_1_2_CREDIT))
        elif invalidity_level == "3":
            taxpayer_credits += MONTHLY_INVALIDITY_3_CREDIT
            credit_items.append(("Invalidita III. stupně", MONTHLY_INVALIDITY_3_CREDIT))
        if taxpayer_ztp:
            taxpayer_credits += MONTHLY_ZTP_CREDIT
            credit_items.append(("Držitel průkazu ZTP/P", MONTHLY_ZTP_CREDIT))

    tax_after_credits = max(0, pre_credit_tax - taxpayer_credits)
    child_tax_credit = 0
    child_credit_items = []
    tax_bonus = 0
    final_tax = tax_after_credits

    if signed_tax_declaration and children:
        child_tax_credit, child_credit_items = calculate_child_tax_credit(children)
        if child_tax_credit <= tax_after_credits:
            final_tax = tax_after_credits - child_tax_credit
        else:
            bonus_candidate = child_tax_credit - tax_after_credits
            if gross_salary >= MONTHLY_BONUS_INCOME_LIMIT and bonus_candidate >= 50:
                tax_bonus = bonus_candidate
                final_tax = 0
            else:
                final_tax = 0

    net_salary = gross_salary - social_insurance - health_insurance - final_tax + tax_bonus

    assumption_notes = []
    if employment_type == "dpp" and not participates_social:
        assumption_notes.append("U DPP pod 12 000 Kč se v roce 2026 neodvádí sociální ani zdravotní pojištění.")
    if employment_type == "dpc" and not participates_social:
        assumption_notes.append("U DPČ pod 4 500 Kč se v roce 2026 standardně neodvádí sociální ani zdravotní pojištění.")
    if minimum_health_applies:
        assumption_notes.append("Protože jde o pracovní poměr a nevztahuje se výjimka z minima, dopočítává se zdravotní pojištění do minimální mzdy.")
    if not signed_tax_declaration:
        assumption_notes.append("Bez podepsaného Prohlášení k dani se neuplatňuje sleva na poplatníka ani daňové zvýhodnění na děti.")

    student_note = None
    if inputs["student"]:
        student_note = (
            "Sleva na studenta byla zrušena od 1. 1. 2024, proto už v roce 2026 nemění výpočet daně. "
            "Student ale často spadá mezi státní pojištěnce, takže může ovlivnit minimum zdravotního pojištění."
        )

    breakdown_rows = [
        ("Hrubá mzda", gross_salary),
        ("Sociální pojištění zaměstnance", -social_insurance),
        ("Zdravotní pojištění zaměstnance", -health_insurance),
        ("Daň po slevách", -final_tax if final_tax else 0),
    ]
    if tax_bonus:
        breakdown_rows.append(("Daňový bonus na děti", tax_bonus))

    return {
        **inputs,
        "employment_type_options": EMPLOYMENT_TYPE_OPTIONS,
        "health_exemption_options": HEALTH_EXEMPTION_OPTIONS,
        "child_count": len(children),
        "net_salary_result": {
            "gross_salary": format_czk(gross_salary),
            "net_salary": format_czk(net_salary),
            "social_insurance": format_czk(social_insurance),
            "health_insurance": format_czk(health_insurance),
            "health_minimum_top_up": format_czk(health_minimum_top_up),
            "pre_credit_tax": format_czk(pre_credit_tax),
            "final_tax": format_czk(final_tax),
            "tax_bonus": format_czk(tax_bonus),
            "tax_base": format_czk(tax_base),
            "minimum_wage": format_czk(MIN_WAGE_2026),
            "tax_threshold": format_czk(HIGHER_TAX_THRESHOLD_MONTHLY),
            "social_rate": format_percent(SOCIAL_INSURANCE_RATE * 100),
            "health_rate": format_percent(HEALTH_INSURANCE_EMPLOYEE_RATE * 100),
        },
        "summary_cards": [
            {"label": "Čistá mzda", "value": format_czk(net_salary)},
            {"label": "Daň po slevách", "value": format_czk(final_tax)},
            {"label": "Sociální pojištění", "value": format_czk(social_insurance)},
            {"label": "Zdravotní pojištění", "value": format_czk(health_insurance)},
        ],
        "credit_items": [{"label": label, "value": format_czk(amount)} for label, amount in credit_items],
        "child_credit_items": [{"label": item["label"], "value": format_czk(item["amount"])} for item in child_credit_items],
        "breakdown_rows": [{"label": label, "value": format_czk(value)} for label, value in breakdown_rows],
        "meta": {
            "participates_social": participates_social,
            "participates_health": participates_health,
            "minimum_health_applies": minimum_health_applies,
            "student_note": student_note,
            "assumption_notes": assumption_notes,
        },
    }
