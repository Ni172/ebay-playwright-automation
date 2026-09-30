import re
from dataclasses import dataclass
from decimal import Decimal

USD_PRICE_PATTERN = re.compile(
    r"""
    (?:US\s*\$|USD\s*|\$)            # Accepted USD prefixes.
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


def parse_price(text: str, currency: str = "USD") -> Money:
    """Parse a single en-US USD price; reject ranges and other currencies.

    A bare $ is interpreted as USD only within the configured USD context.
    """
    if currency != "USD":
        raise ValueError("Only USD parsing is supported")
    normalized = " ".join(text.split())
    match = USD_PRICE_PATTERN.fullmatch(normalized)
    if not match:
        raise ValueError(f"Expected one unambiguous USD price, received {text!r}")
    amount_text = match.group("amount").replace(",", "")
    return Money(Decimal(amount_text), currency)
