"""Search-page interactions and result-card locators for eBay."""

import logging
from decimal import Decimal
from urllib.parse import urljoin

from playwright.sync_api import Locator, Response
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from pages.base_page import BasePage
from utils.money import parse_price

LOGGER = logging.getLogger(__name__)


class EbaySearchError(RuntimeError):
    """Raised when eBay returns its error page after the bounded recovery attempt."""


class SearchResultsPage(BasePage):
    """Search eBay using the visible search controls."""

    _RESULT_CARDS_XPATH = "xpath=//li[contains(@class, 's-card')]"
    _RESULT_LINK_XPATH = "xpath=.//a[contains(@class, 's-card__link')][@href]"
    _RESULT_PRICE_XPATH = "xpath=(.//*[contains(@class, 's-card__price')])[1]"
    _SEARCH_INPUT_PLACEHOLDER = "Search for anything"
    _SHIPPING_DIALOG_TEXT = "Are you shipping to"
    _CONFIRM_BUTTON_NAME = "Confirm"
    _MAX_PRICE_INPUT = "input[aria-label*='Max'], input[name*='maxPrice']"
    _APPLY_PRICE_BUTTON = "button:has-text('Apply')"
    _PRICE_FILTER_CONTROL = "button:has-text('Price'), summary:has-text('Price')"
    _NEXT_PAGE_XPATH = (
        "xpath=//a[contains(@class, 'pagination__next') and @href and not(@aria-disabled='true')]"
    )

    @property
    def search_input(self) -> Locator:
        """Return the global search field from the current page."""
        return self.page.get_by_placeholder(self._SEARCH_INPUT_PLACEHOLDER, exact=True)

    @property
    def shipping_destination_dialog(self) -> Locator:
        """Return eBay's optional shipping-destination confirmation dialog."""
        return self.page.get_by_role("dialog").filter(has_text=self._SHIPPING_DIALOG_TEXT)

    def open_search_home(self) -> Response:
        """Open the eBay home page that contains the global search form."""
        response = self.open("/")
        self.confirm_shipping_destination_if_present(wait_timeout_ms=2_000)
        return response

    def search(self, query: str) -> None:
        """Submit a query, recovering once through eBay's Go to homepage control."""
        if not query.strip():
            raise ValueError("Search query must not be empty")

        self._submit_search(query)
        if self._wait_for_search_outcome(query) == "results":
            return

        if not self.error_page.go_to_home_if_displayed():
            raise EbaySearchError("eBay displayed an unrecognized search error page")

        LOGGER.warning("eBay returned its error page; retrying the search once from the homepage")
        self._submit_search(query)
        if self._wait_for_search_outcome(query) != "results":
            raise EbaySearchError("eBay returned its search error page again after recovery")

    def _submit_search(self, query: str) -> None:
        self.confirm_shipping_destination_if_present()
        self.search_input.fill(query)
        self.confirm_shipping_destination_if_present()
        self.search_input.press("Enter")

    def _wait_for_search_outcome(self, query: str) -> str:
        outcome = self.page.wait_for_function(
            """
            ({ query, errorText }) => {
                const title = document.title;
                if (title.toLowerCase().includes(query) && title.includes('eBay')) {
                    return 'results';
                }
                if ((document.body?.innerText || '').includes(errorText)) {
                    return 'error';
                }
                return false;
            }
            """,
            arg={"query": query.casefold(), "errorText": self.error_page.MESSAGE},
        )
        return outcome.json_value()

    def confirm_shipping_destination_if_present(self, wait_timeout_ms: int = 0) -> bool:
        """Confirm eBay's already displayed shipping destination when its dialog is open."""
        dialog = self.shipping_destination_dialog
        try:
            if wait_timeout_ms:
                dialog.wait_for(state="visible", timeout=wait_timeout_ms)
            elif not dialog.is_visible():
                return False
        except PlaywrightTimeoutError:
            return False

        confirm_button = dialog.get_by_role("button", name=self._CONFIRM_BUTTON_NAME, exact=True)
        if not confirm_button.is_visible():
            return False

        confirm_button.click()
        dialog.wait_for(state="hidden")
        return True

    def search_items_by_name_under_price(
        self, query: str, max_price: Decimal, limit: int = 5
    ) -> list[str]:
        """Search, apply eBay's available max-price filter, and collect matching URLs.

        The page filter is optional because eBay can vary its result-page layout.  The
        card-level price check remains the final decision for every returned URL.
        """
        self._validate_limits(max_price, limit)
        self.open_search_home()
        self.search(query)
        self.apply_max_price_filter(max_price)

        eligible_urls: list[str] = []
        seen_urls: set[str] = set()
        visited_pages: set[str] = set()

        while self.page.url not in visited_pages and len(eligible_urls) < limit:
            visited_pages.add(self.page.url)
            self._append_eligible_urls(eligible_urls, seen_urls, max_price, limit)
            if len(eligible_urls) == limit or not self.go_to_next_results_page():
                break

        return eligible_urls

    def apply_max_price_filter(self, max_price: Decimal) -> bool:
        """Use the visible eBay max-price control when the current layout offers it."""
        max_input = self.page.locator(self._MAX_PRICE_INPUT).first
        try:
            max_input.wait_for(state="visible", timeout=2_000)
        except PlaywrightTimeoutError:
            price_control = self.page.locator(self._PRICE_FILTER_CONTROL).first
            if not price_control.count() or not price_control.is_visible():
                return False
            price_control.click()
            try:
                max_input.wait_for(state="visible", timeout=2_000)
            except PlaywrightTimeoutError:
                return False

        max_input.fill(str(max_price))
        apply_button = self.page.locator(self._APPLY_PRICE_BUTTON).first
        if not apply_button.is_visible():
            return False

        current_url = self.page.url
        apply_button.click()
        self._wait_for_results_change(current_url)
        return True

    def go_to_next_results_page(self) -> bool:
        """Advance one result page when eBay exposes an enabled Next link."""
        next_page = self.page.locator(self._NEXT_PAGE_XPATH).first
        if not next_page.count() or not next_page.is_visible():
            return False

        current_url = self.page.url
        next_page.click()
        return self._wait_for_results_change(current_url)

    @property
    def result_cards(self) -> Locator:
        """Return result cards through XPath, as required by the assignment."""
        return self.page.locator(self._RESULT_CARDS_XPATH)

    def collect_eligible_product_urls(self, max_price: Decimal, limit: int) -> list[str]:
        """Return unique loaded-card URLs priced at or below the ILS limit.

        Price ranges and malformed prices are intentionally excluded rather than guessed.
        Pagination belongs to search_items_by_name_under_price; this method reads one page.
        """
        self._validate_limits(max_price, limit)
        eligible_urls: list[str] = []
        self._append_eligible_urls(eligible_urls, set(), max_price, limit)
        return eligible_urls

    def _append_eligible_urls(
        self, eligible_urls: list[str], seen_urls: set[str], max_price: Decimal, limit: int
    ) -> None:
        for index in range(self.result_cards.count()):
            card = self.result_cards.nth(index)
            price_locator = card.locator(self._RESULT_PRICE_XPATH)
            # eBay can render several carousel-image links for one product card.
            # The first product link identifies the card; duplicate URLs are removed below.
            link_locator = card.locator(self._RESULT_LINK_XPATH).first
            if not price_locator.count() or not link_locator.count():
                continue

            try:
                price = parse_price(price_locator.inner_text())
            except ValueError:
                continue
            if price.amount > max_price:
                continue

            href = link_locator.get_attribute("href")
            url = urljoin(self.page.url, href) if href else None
            if not url or url in seen_urls:
                continue

            eligible_urls.append(url)
            seen_urls.add(url)
            if len(eligible_urls) == limit:
                break

    @staticmethod
    def _validate_limits(max_price: Decimal, limit: int) -> None:
        if not max_price.is_finite() or max_price <= 0:
            raise ValueError("max_price must be finite and positive")
        if limit <= 0:
            raise ValueError("limit must be positive")

    def _wait_for_results_change(self, previous_url: str) -> bool:
        try:
            self.page.wait_for_url(lambda url: url != previous_url, timeout=5_000)
            self.page.wait_for_load_state("domcontentloaded")
        except PlaywrightTimeoutError:
            return False
        return True
