import re
from dataclasses import dataclass
from decimal import Decimal

ILS_PRICE_PATTERN = re.compile(
    r"""
    (?:₪|ILS\s*)                       # Accepted Israeli-shekel prefixes.
    \s*
    (?P<amount>
        (?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)  # Grouped or plain whole amount.
        (?:\.[0-9]{2})?              # Optional cents, exactly two digits.
    )
    """,
    re.VERBOSE,
)


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str


def parse_price(text: str, currency: str = "ILS") -> Money:
    """Parse one ILS price as displayed in the agreed Israeli eBay context."""
    if currency != "ILS":
        raise ValueError("Only ILS parsing is supported")
    normalized = " ".join(text.split())
    match = ILS_PRICE_PATTERN.fullmatch(normalized)
    if not match:
        raise ValueError(f"Expected one unambiguous ILS price, received {text!r}")
    amount_text = match.group("amount").replace(",", "")
    return Money(Decimal(amount_text), currency)
