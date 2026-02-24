"""INN validation and normalisation utilities."""
import re


def normalize_inn(raw: str) -> str:
    """Strip everything but digits."""
    return re.sub(r"\D", "", raw)


def _checksum(inn: str, coefficients: list[int]) -> int:
    total = sum(int(inn[i]) * c for i, c in enumerate(coefficients))
    return (total % 11) % 10


def validate_inn(inn: str) -> bool:
    """Return True if INN checksum is correct (10 or 12 digits)."""
    if not inn.isdigit():
        return False
    if len(inn) == 10:
        c = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        return _checksum(inn, c) == int(inn[9])
    if len(inn) == 12:
        c1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        c2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        return (
            _checksum(inn, c1) == int(inn[10])
            and _checksum(inn, c2) == int(inn[11])
        )
    return False
