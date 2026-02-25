import re


def is_valid_inn_ogrn(text: str) -> bool:
    """ИНН (10/12 digits) or ОГРН (13/15 digits)."""
    text = text.strip()
    if not text.isdigit():
        return False
    return len(text) in (10, 12, 13, 15)


def is_valid_phone(text: str) -> bool:
    """Loose phone check — DaData does the real work."""
    return bool(re.match(r"^\+?\d[\d\s()\-]{5,19}\d$", text.strip()))


def is_valid_passport(text: str) -> bool:
    """4 digits (series) + 6 digits (number), optional space."""
    return bool(re.match(r"^\d{4}\s?\d{6}$", text.strip()))


def is_valid_vehicle(text: str) -> bool:
    """At least 3 chars — DaData does the real work."""
    return len(text.strip()) >= 3
