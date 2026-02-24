"""Masking helpers for privacy-sensitive data."""

import hashlib


def mask_phone(phone: str | None) -> str:
    """'+7 916 123-45-67' → '+7 916 ***-**-67'"""
    if not phone:
        return "—"
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) < 6:
        return "***"
    return digits[:4] + "****" + digits[-2:]


def mask_passport_series(series: str | None) -> str:
    if not series or len(series) < 2:
        return "**"
    return "**" + series[-2:]


def mask_passport_number(number: str | None) -> str:
    if not number or len(number) < 2:
        return "****"
    return "****" + number[-2:]


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()
