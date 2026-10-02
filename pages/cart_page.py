"""Read the Subtotal displayed in eBay's cart summary."""

import re
from dataclasses import dataclass

from playwright.sync_api import Locator

from pages.base_page import BasePage
from utils.money import Money, parse_price


@dataclass(frozen=True)
class CartSummary:
    items_count: int
    subtotal: Money


class CartPage(BasePage):
    """Keep cart navigation and displayed-value extraction out of assertions."""

    _CART_URL = "https://cart.ebay.com/"
    _CART_SUMMARY_SELECTOR = '[data-test-id="cart-summary"]'
    _ITEMS_ROW_SELECTOR = ".cart-summary-line-item"
    _SUBTOTAL_SELECTOR = '[data-test-id="SUBTOTAL"]'

    @property
    def cart_summary(self) -> Locator:
        """Return eBay's order-summary region."""
        return self.page.locator(self._CART_SUMMARY_SELECTOR)

    @property
    def items_row(self) -> Locator:
        """Return the item-count row within the order summary."""
        return self.cart_summary.locator(self._ITEMS_ROW_SELECTOR).filter(
            has_text=re.compile(r"^Items\s*\(\d+\)")
        )

    @property
    def subtotal(self) -> Locator:
        """Return the displayed cart Subtotal value."""
        return self.cart_summary.locator(self._SUBTOTAL_SELECTOR)

    def read_summary(self) -> CartSummary:
        """Open the cart and read its displayed item count and Subtotal."""
        self.open(self._CART_URL)
        # Items supplies the count; SUBTOTAL includes eBay's displayed shipping charge.
        self.items_row.wait_for(state="visible")
        text = " ".join(self.items_row.inner_text().split())
        match = re.match(r"Items\s*\((\d+)\)", text)
        if match is None:
            raise ValueError(f"Unrecognized cart items summary: {text!r}")
        self.subtotal.wait_for(state="visible")
        return CartSummary(
            items_count=int(match.group(1)),
            subtotal=parse_price(self.subtotal.inner_text()),
        )
