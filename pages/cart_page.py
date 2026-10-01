"""Read the Subtotal displayed in eBay's cart summary."""

import re
from dataclasses import dataclass

from pages.base_page import BasePage
from utils.money import Money, parse_price


@dataclass(frozen=True)
class CartSummary:
    items_count: int
    subtotal: Money


class CartPage(BasePage):
    """Keep cart navigation and displayed-value extraction out of assertions."""

    def read_summary(self) -> CartSummary:
        self.open("https://cart.ebay.com/")
        # Items supplies the count; SUBTOTAL includes eBay's displayed shipping charge.
        items_row = self.page.locator(".cart-summary-line-item").filter(
            has_text=re.compile(r"Items\s*\(\d+\)")
        )
        items_row.wait_for(state="visible")
        text = " ".join(items_row.inner_text().split())
        match = re.fullmatch(r"Items\s*\((\d+)\)\s*(.+)", text)
        if match is None:
            raise ValueError(f"Unrecognized cart items summary: {text!r}")
        subtotal = self.page.locator('[data-test-id="SUBTOTAL"]')
        subtotal.wait_for(state="visible")
        return CartSummary(
            items_count=int(match.group(1)),
            subtotal=parse_price(subtotal.inner_text()),
        )
