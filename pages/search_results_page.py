"""Search-page interactions and result-card locators for eBay."""

import re

from playwright.sync_api import Locator, Page, Response

from pages.base_page import BasePage


class SearchResultsPage(BasePage):
    """Search eBay using the visible search controls."""

    _RESULTS_URL = re.compile(r".*/sch/i\.html(?:\?.*)?$")
    _RESULT_CARDS_XPATH = (
        "xpath=//li[contains(concat(' ', normalize-space(@class), ' '), ' s-card ')]"
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
