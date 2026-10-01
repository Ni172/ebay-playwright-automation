"""Live coverage for search submission, price filtering, and pagination."""

from urllib.parse import parse_qs, urlsplit

import pytest
from playwright.sync_api import expect

from pages.search_results_page import SearchResultsPage
from utils.data_loader import SearchCase

pytestmark = pytest.mark.e2e


def test_search_collects_items_under_price(page, search_case, screenshot):
    search_page = SearchResultsPage(page)

    print(f"Search {search_case.query!r} for items at or under ILS {search_case.max_price}")
    urls = search_page.search_items_by_name_under_price(
        search_case.query, search_case.max_price, search_case.limit
    )
    print(f"Collected {len(urls)} eligible URLs")
    _assert_search_submitted(page, search_page, search_case.query)
    _assert_urls(urls, search_case)
    if search_case.expected_page_count > 1:
        assert len(search_page.last_visited_results_pages) == search_case.expected_page_count
        assert len(set(search_page.last_visited_results_pages)) == search_case.expected_page_count
        assert sum(search_page.last_eligible_counts_by_page) == len(urls)
        assert search_page.last_eligible_counts_by_page[0] < search_case.limit
        for page_number, (page_url, eligible_count) in enumerate(
            zip(
                search_page.last_visited_results_pages,
                search_page.last_eligible_counts_by_page,
                strict=True,
            ),
            start=1,
        ):
            print(f"Results page {page_number}: {page_url}; eligible URLs: {eligible_count}")
    screenshot(f"eligible-search-results-{search_case.id}")


def test_search_rejects_invalid_request_before_navigation(page, negative_search_case):
    search_page = SearchResultsPage(page)
    initial_url = page.url

    with pytest.raises(ValueError, match=negative_search_case.expected_message):
        search_page.search_items_by_name_under_price(
            negative_search_case.query,
            negative_search_case.max_price,
            negative_search_case.limit,
        )

    assert page.url == initial_url


def _assert_search_submitted(page, search_page: SearchResultsPage, query: str) -> None:
    query_parameters = parse_qs(urlsplit(page.url).query)
    assert query_parameters.get("_nkw") == [query]
    expect(search_page.search_input).to_have_value(query)


def _assert_urls(urls: list[str], search_case: SearchCase) -> None:
    assert search_case.expected_min_results <= len(urls) <= search_case.expected_max_results
    assert len(urls) <= search_case.limit
    assert len(urls) == len(set(urls))
    assert all(url.startswith("https://www.ebay.com/") for url in urls)
