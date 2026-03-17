from werkzeug.exceptions import BadRequest


def _format_limit(value):
    if isinstance(value, int) or (isinstance(value, float) and value.is_integer()):
        return str(int(value))
    return str(value).replace(".", ",")


def parse_float(req, key, default, label, min_value=None, max_value=None):
    raw_value = req.values.get(key, default)
    try:
        value = float(raw_value)
    except (TypeError, ValueError) as exc:
        raise BadRequest(f"Pole '{label}' musí být číslo.") from exc

    if min_value is not None and value < min_value:
        raise BadRequest(f"Pole '{label}' musí být alespoň {_format_limit(min_value)}.")
    if max_value is not None and value > max_value:
        raise BadRequest(f"Pole '{label}' může být nejvýše {_format_limit(max_value)}.")
    return value


def parse_int(req, key, default, label, min_value=None, max_value=None):
    raw_value = req.values.get(key, default)
    try:
        value = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise BadRequest(f"Pole '{label}' musí být celé číslo.") from exc

    if min_value is not None and value < min_value:
        raise BadRequest(f"Pole '{label}' musí být alespoň {_format_limit(min_value)}.")
    if max_value is not None and value > max_value:
        raise BadRequest(f"Pole '{label}' může být nejvýše {_format_limit(max_value)}.")
    return value


def parse_choice(req, key, default, allowed_values, label):
    value = req.values.get(key, default)
    if value not in allowed_values:
        raise BadRequest(f"Pole '{label}' obsahuje nepovolenou hodnotu.")
    return value


def parse_choice_list(req, key, allowed_values, label, max_items=None):
    values = req.values.getlist(key)
    if max_items is not None and len(values) > max_items:
        raise BadRequest(f"Pole '{label}' může obsahovat nejvýše {_format_limit(max_items)} položek.")

    for value in values:
        if value not in allowed_values:
            raise BadRequest(f"Pole '{label}' obsahuje nepovolenou hodnotu.")
    return values


def validate_less_or_equal(value, other_value, label, other_label):
    if value > other_value:
        raise BadRequest(f"Pole '{label}' nemůže být vyšší než pole '{other_label}'.")
