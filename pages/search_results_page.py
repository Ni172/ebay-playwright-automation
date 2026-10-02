"""Search-page interactions and result-card locators for eBay."""

import logging
from decimal import Decimal, InvalidOperation
from urllib.parse import parse_qs, urljoin, urlsplit

from playwright.sync_api import Locator, Page, Response
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from pages.base_page import BasePage
from utils.money import parse_price

LOGGER = logging.getLogger(__name__)


class EbaySearchError(RuntimeError):
    """Raised when eBay cannot provide the requested search results."""


class SearchResultsPage(BasePage):
    """Search eBay using the visible search controls."""

    _RESULT_CARDS_XPATH = "xpath=//li[contains(@class, 's-card')]"
    _RESULT_LINK_XPATH = "xpath=.//a[contains(@class, 's-card__link')][@href]"
    _RESULT_PRICE_XPATH = "xpath=(.//*[contains(@class, 's-card__price')])[1]"
    _SEARCH_INPUT_PLACEHOLDER = "Search for anything"
    _SHIPPING_DIALOG_TEXT = "Are you shipping to"
    _CONFIRM_BUTTON_NAME = "Confirm"
    _MIN_PRICE_INPUT_LABEL = "Minimum Value in ILS"
    _MAX_PRICE_INPUT_LABEL = "Maximum Value in ILS"
    _SUBMIT_PRICE_RANGE_XPATH = "xpath=//button[@title='Submit price range']"
    _PRICE_FILTER_CONTROL = "button:has-text('Price'), summary:has-text('Price')"
    _NEXT_PAGE_XPATH = (
        "xpath=//a[contains(@class, 'pagination__next') and @href and not(@aria-disabled='true')]"
    )
    _SEARCH_ATTEMPTS = 2
    _RESULTS_CHANGE_TIMEOUT_MS = 30_000

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._last_visited_results_pages: tuple[str, ...] = ()
        self._last_eligible_counts_by_page: tuple[int, ...] = ()

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
        """Submit a query and wait until eBay shows results or its known error page."""
        self._validate_query(query)

        self._submit_search(query)
        if self._wait_for_search_outcome(query) == "results":
            return
        raise EbaySearchError("eBay returned its error page after search submission")

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
        self._validate_query(query)
        self._validate_limits(max_price, limit)
        self._last_visited_results_pages = ()
        self._last_eligible_counts_by_page = ()
        for attempt in range(self._SEARCH_ATTEMPTS):
            try:
                self.open_search_home()
                self.search(query)
                self.apply_max_price_filter(max_price)
                return self._collect_eligible_urls_across_pages(max_price, limit)
            except EbaySearchError as exc:
                if not self.error_page.go_to_home_if_displayed():
                    raise
                if attempt + 1 == self._SEARCH_ATTEMPTS:
                    raise EbaySearchError(
                        "eBay returned its error page after the configured full-search retries"
                    ) from exc
                LOGGER.warning(
                    "eBay returned its error page; restarting the full search (%d/%d)",
                    attempt + 2,
                    self._SEARCH_ATTEMPTS,
                )

        raise AssertionError("The configured full-search retry loop should always return or raise")

    def _collect_eligible_urls_across_pages(self, max_price: Decimal, limit: int) -> list[str]:
        """Collect eligible URLs through pagination after a successful filtered search."""
        eligible_urls: list[str] = []
        seen_urls: set[str] = set()
        visited_pages: list[str] = []
        eligible_counts_by_page: list[int] = []
        seen_pages: set[str] = set()

        while self.page.url not in seen_pages and len(eligible_urls) < limit:
            visited_pages.append(self.page.url)
            seen_pages.add(self.page.url)
            self._last_visited_results_pages = tuple(visited_pages)
            count_before_page = len(eligible_urls)
            self._append_eligible_urls(eligible_urls, seen_urls, max_price, limit)
            eligible_counts_by_page.append(len(eligible_urls) - count_before_page)
            self._last_eligible_counts_by_page = tuple(eligible_counts_by_page)
            if len(eligible_urls) == limit or not self.go_to_next_results_page():
                break

        return eligible_urls

    @property
    def last_visited_results_pages(self) -> tuple[str, ...]:
        """Return the ordered result pages observed during the latest search."""
        return self._last_visited_results_pages

    @property
    def last_eligible_counts_by_page(self) -> tuple[int, ...]:
        """Return how many unique eligible URLs each visited page contributed."""
        return self._last_eligible_counts_by_page

    def apply_max_price_filter(self, max_price: Decimal) -> bool:
        """Use the visible eBay max-price control when the current layout offers it."""
        min_input = self.page.get_by_role("textbox", name=self._MIN_PRICE_INPUT_LABEL, exact=True)
        max_input = self.page.get_by_role("textbox", name=self._MAX_PRICE_INPUT_LABEL, exact=True)
        try:
            min_input.wait_for(state="visible", timeout=2_000)
            max_input.wait_for(state="visible", timeout=2_000)
        except PlaywrightTimeoutError:
            price_control = self.page.locator(self._PRICE_FILTER_CONTROL).first
            if not price_control.count() or not price_control.is_visible():
                return False
            price_control.click()
            try:
                min_input.wait_for(state="visible", timeout=2_000)
                max_input.wait_for(state="visible", timeout=2_000)
            except PlaywrightTimeoutError:
                return False

        max_price_text = format(max_price.normalize(), "f")
        self._type_price_value(min_input, "0")
        self._type_price_value(max_input, max_price_text)
        if max_input.input_value() != max_price_text:
            raise EbaySearchError("eBay did not retain the requested maximum-price input")

        submit_button = self.page.locator(self._SUBMIT_PRICE_RANGE_XPATH)
        try:
            submit_button.wait_for(state="visible", timeout=2_000)
        except PlaywrightTimeoutError as exc:
            message = "eBay price inputs are visible but submit is unavailable"
            raise EbaySearchError(message) from exc

        current_url = self.page.url
        submit_button.click()
        if not self._wait_for_results_change(current_url):
            raise EbaySearchError("eBay price filter did not change the results page")
        self._assert_max_price_in_url(max_price)
        return True

    @staticmethod
    def _type_price_value(price_input: Locator, value: str) -> None:
        """Enter a price through keyboard events and commit it by leaving the field."""
        price_input.click()
        price_input.press("Control+A")
        price_input.press("Backspace")
        # eBay's controlled price inputs can discard values injected by fill().
        price_input.press_sequentially(value, delay=50)
        price_input.press("Tab")

    def _assert_max_price_in_url(self, max_price: Decimal) -> None:
        query_parameters = parse_qs(urlsplit(self.page.url).query)
        applied_values = query_parameters.get("_udhi")
        if not applied_values:
            raise EbaySearchError("eBay did not apply the requested maximum-price filter")
        try:
            applied_max_price = Decimal(applied_values[0])
        except InvalidOperation as exc:
            raise EbaySearchError("eBay returned an invalid maximum-price filter value") from exc
        if applied_max_price != max_price:
            raise EbaySearchError(
                f"eBay applied maximum price {applied_max_price} instead of {max_price}"
            )

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
        if not isinstance(max_price, Decimal) or not max_price.is_finite() or max_price <= 0:
            raise ValueError("max_price must be finite and positive")
        if type(limit) is not int or limit <= 0:
            raise ValueError("limit must be a positive integer")

    @staticmethod
    def _validate_query(query: str) -> None:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Search query must not be empty")

    def _wait_for_results_change(self, previous_url: str) -> bool:
        try:
            self.page.wait_for_url(
                lambda url: url != previous_url,
                timeout=self._RESULTS_CHANGE_TIMEOUT_MS,
            )
            self.page.wait_for_load_state("domcontentloaded")
        except PlaywrightTimeoutError:
            return False
        if self.error_page.is_displayed():
            raise EbaySearchError(
                "eBay returned its error page after price filtering or pagination"
            )
        return True
