"""Live eBay scenario that searches for products and adds every result to the cart."""

import pytest

from flows.shopping_flow import ShoppingFlow
from pages.search_results_page import SearchResultsPage

pytestmark = pytest.mark.e2e


def test_searches_and_adds_every_eligible_item(page, cart_case, rng, screenshot):
    search_page = SearchResultsPage(page)

    print(
        f"Search {cart_case.query!r} for {cart_case.limit} items "
        f"at or under ILS {cart_case.max_price}; add every returned URL"
    )
    urls = search_page.search_items_by_name_under_price(
        cart_case.query,
        cart_case.max_price,
        cart_case.limit,
    )
    assert len(urls) == cart_case.limit
    print(f"Collected {len(urls)} URLs; add every URL")

    shopping_flow = ShoppingFlow(page, rng, screenshot)
    added_items = shopping_flow.add_items_to_cart(urls)

    assert [item.url for item in added_items] == urls
    for item_number, item in enumerate(added_items, start=1):
        variant_summary = ", ".join(f"{variant.name}={variant.value}" for variant in item.variants)
        item_summary = f"Confirmed item {item_number}/{len(urls)}: {item.url};"
        item_summary += f" variants={variant_summary or 'none'}"
        print(item_summary)


def test_add_items_to_cart_rejects_invalid_urls_before_navigation(
    page, rng, screenshot, invalid_cart_case
):
    shopping_flow = ShoppingFlow(page, rng, screenshot)
    initial_url = page.url

    with pytest.raises(ValueError, match=invalid_cart_case.expected_message):
        shopping_flow.add_items_to_cart(invalid_cart_case.urls)

    assert page.url == initial_url
