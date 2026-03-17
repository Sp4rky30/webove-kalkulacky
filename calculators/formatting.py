def format_czk(value: float) -> str:
    return f"{value:,.0f} Kč".replace(",", " ")


def format_percent(value: float) -> str:
    return f"{value:.1f} %".replace(".", ",")


def format_number(value: float) -> str:
    return f"{value:,.0f}".replace(",", " ")
