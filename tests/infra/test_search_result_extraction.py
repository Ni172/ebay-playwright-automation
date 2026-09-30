"""Verify XPath result extraction against local eBay-shaped HTML."""

from decimal import Decimal

import pytest

from pages.search_results_page import SearchResultsPage

pytestmark = pytest.mark.infra


def test_collects_unique_eligible_ils_urls_with_xpath(page):
    page.set_content(
        """
        <ul>
          <li class="s-card"><a class="s-card__link" href="https://items.example/one">One</a>
            <span class="s-card__price">₪199.00</span></li>
          <li class="s-card">
            <a class="s-card__link" href="https://items.example/carousel">Image one</a>
            <a class="s-card__link" href="https://items.example/carousel">Image two</a>
            <span class="s-card__price">₪100.00</span></li>
          <li class="s-card"><a class="s-card__link" href="https://items.example/two">Two</a>
            <span class="s-card__price">₪220.00</span></li>
          <li class="s-card"><a class="s-card__link" href="https://items.example/three">Three</a>
            <span class="s-card__price">₪220.01</span></li>
          <li class="s-card"><a class="s-card__link" href="https://items.example/one">Duplicate</a>
            <span class="s-card__price">₪100.00</span></li>
          <li class="s-card"><a class="s-card__link" href="https://items.example/range">Range</a>
            <span class="s-card__price">₪10.00 to ₪20.00</span></li>
        </ul>
        """
    )

    search_page = SearchResultsPage(page)

    assert search_page.collect_eligible_product_urls(Decimal("220.00"), limit=5) == [
        "https://items.example/one",
        "https://items.example/carousel",
        "https://items.example/two",
    ]


@pytest.mark.parametrize("max_price,limit", [(Decimal("0"), 1), (Decimal("10"), 0)])
def test_rejects_invalid_extraction_limits(page, max_price, limit):
    search_page = SearchResultsPage(page)

    with pytest.raises(ValueError):
        search_page.collect_eligible_product_urls(max_price, limit)


def test_searches_filters_and_collects_across_result_pages(page, monkeypatch):
    first_page = "https://results.example/sch/i.html?_nkw=shoes"
    filtered_first_page = f"{first_page}&_udhi=220.00"
    filtered_second_page = f"{filtered_first_page}&_pgn=2"
    pages = {
        first_page: """
            <input aria-label="Max price" />
            <button onclick="location.href='/sch/i.html?_nkw=shoes&_udhi=220.00'">Apply</button>
        """,
        filtered_first_page: """
            <input aria-label="Max price" /><button>Apply</button>
            <li class="s-card"><a class="s-card__link" href="/item/one">One</a>
              <span class="s-card__price">₪199.00</span></li>
            <li class="s-card"><a class="s-card__link" href="/item/over">Over</a>
              <span class="s-card__price">₪220.01</span></li>
            <a class="pagination__next" href="/sch/i.html?_nkw=shoes&_udhi=220.00&_pgn=2">Next</a>
        """,
        filtered_second_page: """
            <li class="s-card"><a class="s-card__link" href="/item/two">Two</a>
              <span class="s-card__price">₪220.00</span></li>
        """,
    }

    def fulfill_page(route):
        route.fulfill(body=pages[route.request.url], content_type="text/html; charset=utf-8")

    page.route("https://results.example/**", fulfill_page)
    search_page = SearchResultsPage(page)
    monkeypatch.setattr(search_page, "open_search_home", lambda: None)
    monkeypatch.setattr(search_page, "search", lambda query: page.goto(first_page))

    assert search_page.search_items_by_name_under_price("shoes", Decimal("220.00"), limit=5) == [
        "https://results.example/item/one",
        "https://results.example/item/two",
    ]


def test_returns_loaded_results_when_price_filter_is_not_available(page):
    page.set_content(
        """
        <li class="s-card"><a class="s-card__link" href="https://items.example/one">One</a>
          <span class="s-card__price">₪199.00</span></li>
        """
    )
    search_page = SearchResultsPage(page)

    assert search_page.apply_max_price_filter(Decimal("220.00")) is False
    assert search_page.collect_eligible_product_urls(Decimal("220.00"), limit=5) == [
        "https://items.example/one"
    ]


def test_search_waits_for_an_ebay_title_containing_the_query(page):
    page.set_content(
        """
        <title>eBay home | eBay</title>
        <input placeholder="Search for anything"
          onkeydown="if (event.key === 'Enter') document.title='Shoes results | eBay'" />
        """
    )
    search_page = SearchResultsPage(page)

    search_page.search("shoes")

    assert page.title() == "Shoes results | eBay"


def test_confirms_shipping_destination_dialog_when_present(page):
    page.set_content(
        """
        <div role="dialog">
          <h2>Are you shipping to this destination?</h2>
          <button onclick="this.closest('[role=dialog]').remove()">Confirm</button>
        </div>
        """
    )
    search_page = SearchResultsPage(page)

    assert search_page.confirm_shipping_destination_if_present() is True
    assert search_page.shipping_destination_dialog.count() == 0


def test_does_not_require_a_shipping_destination_dialog(page):
    search_page = SearchResultsPage(page)

    assert search_page.confirm_shipping_destination_if_present() is False


def test_waits_for_a_shipping_destination_dialog_that_appears_after_navigation(page):
    page.set_content(
        """
        <script>
          setTimeout(() => {
            document.body.insertAdjacentHTML(
              'beforeend',
              `<div role="dialog"><h2>Are you shipping to this destination?</h2>
                 <button onclick="this.closest('[role=dialog]').remove()">Confirm</button></div>`
            );
          }, 100);
        </script>
        """
    )
    search_page = SearchResultsPage(page)

    assert search_page.confirm_shipping_destination_if_present(wait_timeout_ms=1_000) is True
    assert search_page.shipping_destination_dialog.count() == 0


def test_does_not_follow_a_disabled_next_page_link(page):
    page.set_content(
        '<a class="pagination__next pagination__next--disabled" href="/page-2" '
        'aria-disabled="true">Next</a>'
    )
    search_page = SearchResultsPage(page)

    assert search_page.go_to_next_results_page() is False
