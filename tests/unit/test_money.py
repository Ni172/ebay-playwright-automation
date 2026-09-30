from decimal import Decimal

import pytest

from utils.money import parse_price

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "text, expected",
    [
        ("US $1,234.56", "1234.56"),
        ("$0.10", "0.10"),
        ("USD 220", "220"),
    ],
)
def test_price_preserves_decimal_amount(text, expected):
    price = parse_price(text)
    assert price.amount == Decimal(expected)
    assert price.currency == "USD"


@pytest.mark.parametrize(
    "text",
    [
        "$10 to $20",
        "EUR 20.00",
        "AU $20.00",
        "$1.234,56",
        "$12,34",
        "NaN",
        "-$1.00",
    ],
)
def test_ambiguous_or_unsupported_prices_are_rejected(text):
    with pytest.raises(ValueError):
        parse_price(text)
