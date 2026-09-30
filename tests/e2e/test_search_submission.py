"""Live search submission check; product extraction is a later stage."""

from urllib.parse import parse_qs, urlsplit

import pytest
from playwright.sync_api import expect

from pages.search_results_page import SearchResultsPage

pytestmark = pytest.mark.e2e


def test_search_submits_external_case(page, search_case, screenshot):
    search_page = SearchResultsPage(page)

    print("Open the eBay search homepage")
    response = search_page.open_search_home()
    print(f"Homepage status: {response.status}")
    print(f"Submit search query: {search_case.query}")
    search_page.search(search_case.query)
    print("Confirm the results URL carries the submitted query")
    _assert_search_submitted(page, search_page, search_case.query)
    screenshot("search-results")


def test_search_collects_items_under_price(page, search_case, screenshot):
    search_page = SearchResultsPage(page)

    print(f"Search {search_case.query!r} for items at or under ILS {search_case.max_price}")
    urls = search_page.search_items_by_name_under_price(
        search_case.query, search_case.max_price, search_case.limit
    )
    print(f"Collected {len(urls)} eligible URLs")
    _assert_urls(urls, search_case.limit)
    screenshot("eligible-search-results")


def _assert_search_submitted(page, search_page: SearchResultsPage, query: str) -> None:
    query_parameters = parse_qs(urlsplit(page.url).query)
    assert query_parameters.get("_nkw") == [query]
    expect(search_page.search_input).to_have_value(query)


def _assert_urls(urls: list[str], limit: int) -> None:
    assert len(urls) <= limit
    assert len(urls) == len(set(urls))
    assert all(url.startswith("https://www.ebay.com/") for url in urls)
