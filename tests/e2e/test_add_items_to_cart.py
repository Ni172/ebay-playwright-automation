"""Live eBay scenario that searches for products and adds every result to the cart."""

import pytest

from flows.shopping_flow import ShoppingFlow
from pages.search_results_page import SearchResultsPage

pytestmark = pytest.mark.e2e
RESERVE_CANDIDATES = 3


def test_searches_and_adds_every_eligible_item(page, search_case, rng, screenshot):
    search_page = SearchResultsPage(page)
    candidate_limit = search_case.limit + RESERVE_CANDIDATES

    print(
        f"Search {search_case.query!r} for {search_case.limit} required items "
        f"and up to {RESERVE_CANDIDATES} reserve candidates "
        f"at or under ILS {search_case.max_price}"
    )
    urls = search_page.search_items_by_name_under_price(
        search_case.query,
        search_case.max_price,
        candidate_limit,
    )
    assert len(urls) >= search_case.limit, (
        f"The live shopping scenario requires {search_case.limit} candidates, "
        f"but search returned {len(urls)}"
    )
    candidate_summary = f"Collected {len(urls)} candidate URLs;"
    candidate_summary += f" add exactly {search_case.limit} available products"
    print(candidate_summary)

    shopping_flow = ShoppingFlow(page, rng, screenshot)
    added_items = shopping_flow.add_items_to_cart(
        urls,
        expected_count=search_case.limit,
    )

    assert len(added_items) == search_case.limit
    assert all(item.url in urls for item in added_items)
    print(f"Confirmed all {len(added_items)} required cart additions")
