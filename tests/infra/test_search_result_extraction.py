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
        "https://items.example/two",
    ]


@pytest.mark.parametrize("max_price,limit", [(Decimal("0"), 1), (Decimal("10"), 0)])
def test_rejects_invalid_extraction_limits(page, max_price, limit):
    search_page = SearchResultsPage(page)

    with pytest.raises(ValueError):
        search_page.collect_eligible_product_urls(max_price, limit)
