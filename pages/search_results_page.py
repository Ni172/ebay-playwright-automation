"""Search-page interactions and result-card locators for eBay."""

import re
from decimal import Decimal

from playwright.sync_api import Locator, Page, Response

from pages.base_page import BasePage
from utils.money import parse_price


class SearchResultsPage(BasePage):
    """Search eBay using the visible search controls."""

    _RESULTS_URL = re.compile(r".*/sch/i\.html(?:\?.*)?$")
    _RESULT_CARDS_XPATH = (
        "xpath=//li[contains(concat(' ', normalize-space(@class), ' '), ' s-card ')]"
    )
    _RESULT_LINK_XPATH = (
        "xpath=.//a[contains(concat(' ', normalize-space(@class), ' '), ' s-card__link ')][@href]"
    )
    _RESULT_PRICE_XPATH = (
        "xpath=(.//*[contains(concat(' ', normalize-space(@class), ' '), ' s-card__price ')])[1]"
    )

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        # These user-facing contracts are more maintainable than eBay's internal IDs.
        self.search_input = page.get_by_placeholder("Search for anything", exact=True)
        self.search_button = page.get_by_role("button", name="Search", exact=True)

    def open_search_home(self) -> Response:
        """Open the eBay home page that contains the global search form."""
        return self.open("/")

    def search(self, query: str) -> None:
        """Submit one non-empty search query and wait for the results URL."""
        if not query.strip():
            raise ValueError("Search query must not be empty")

        self.search_input.fill(query)
        self.search_button.click()
        self.page.wait_for_url(self._RESULTS_URL)

    @property
    def result_cards(self) -> Locator:
        """Return result cards through XPath, as required by the assignment."""
        return self.page.locator(self._RESULT_CARDS_XPATH)

    def collect_eligible_product_urls(self, max_price: Decimal, limit: int) -> list[str]:
        """Return unique loaded-card URLs priced at or below the ILS limit.

        Price ranges and malformed prices are intentionally excluded rather than guessed.
        Pagination is a separate step because its live eBay locator is not yet verified.
        """
        if not max_price.is_finite() or max_price <= 0:
            raise ValueError("max_price must be finite and positive")
        if limit <= 0:
            raise ValueError("limit must be positive")

        eligible_urls = []
        seen_urls = set()
        for index in range(self.result_cards.count()):
            card = self.result_cards.nth(index)
            price_locator = card.locator(self._RESULT_PRICE_XPATH)
            link_locator = card.locator(self._RESULT_LINK_XPATH)
            if not price_locator.count() or not link_locator.count():
                continue

            try:
                price = parse_price(price_locator.inner_text())
            except ValueError:
                continue
            if price.amount > max_price:
                continue

            url = link_locator.get_attribute("href")
            if not url or url in seen_urls:
                continue

            eligible_urls.append(url)
            seen_urls.add(url)
            if len(eligible_urls) == limit:
                break

        return eligible_urls
