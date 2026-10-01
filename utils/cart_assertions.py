"""Assignment 4.3 assertions, separate from cart page interactions."""

from collections.abc import Callable
from decimal import Decimal

import allure

from pages.cart_page import CartPage


def assert_cart_total_not_exceeds(
    cart_page: CartPage,
    budget_per_item: Decimal,
    items_count: int,
    screenshot: Callable[[str], None],
) -> None:
    """Compare eBay's displayed ILS Subtotal with the full expected budget."""
    if not isinstance(budget_per_item, Decimal) or not budget_per_item.is_finite():
        raise ValueError("budget_per_item must be a finite Decimal")
    if budget_per_item <= 0:
        raise ValueError("budget_per_item must be positive")
    if type(items_count) is not int or items_count <= 0:
        raise ValueError("items_count must be a positive integer")

    with allure.step("Verify cart item count and ILS subtotal"):
        try:
            summary = cart_page.read_summary()
            threshold = budget_per_item * items_count
            print(
                f"Cart: {summary.items_count} items; subtotal ILS {summary.subtotal.amount}; "
                f"budget ILS {budget_per_item} x {items_count} = {threshold}"
            )
            assert summary.items_count == items_count, (
                f"Expected {items_count} cart items, found {summary.items_count}"
            )
            assert summary.subtotal.amount > 0, "A populated cart must have a positive subtotal"
            assert summary.subtotal.amount <= threshold, (
                f"Cart subtotal ILS {summary.subtotal.amount} exceeds budget ILS {threshold}"
            )
        finally:
            screenshot("cart-subtotal")
