"""Tests for INN validation utilities."""
import pytest

from services.inn_utils import normalize_inn, validate_inn


# ── normalize_inn ────────────────────────────────────────────────────────────

def test_normalize_strips_spaces():
    assert normalize_inn("77 07 08 39 12") == "7707083912"


def test_normalize_strips_dashes():
    assert normalize_inn("770-708-391-2") == "7707083912"


def test_normalize_pure_digits():
    assert normalize_inn("7707083912") == "7707083912"


# ── 10-digit INN ─────────────────────────────────────────────────────────────

def test_valid_10_digit_inn():
    # Сбербанк
    assert validate_inn("7707083893") is True


def test_invalid_10_digit_inn_bad_checksum():
    assert validate_inn("7707083894") is False


def test_wrong_length_9_digits():
    assert validate_inn("770708389") is False


# ── 12-digit INN ─────────────────────────────────────────────────────────────

def test_valid_12_digit_inn():
    # Public example valid 12-digit INN
    assert validate_inn("500100732259") is True


def test_invalid_12_digit_inn_bad_checksum():
    assert validate_inn("500100732250") is False


def test_wrong_length_11_digits():
    assert validate_inn("50010073225") is False


# ── edge cases ────────────────────────────────────────────────────────────────

def test_empty_string_is_invalid():
    assert validate_inn("") is False


def test_non_digit_inn_invalid():
    assert validate_inn("abcdefghij") is False
