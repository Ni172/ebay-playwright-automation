"""Cross-page coordination for adding searched products to the cart."""

import logging
import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from urllib.parse import urlsplit

from playwright.sync_api import Page, Response

from pages.base_page import EbayNavigationError
from pages.ebay_error_page import EbayErrorPage
from pages.product_page import ProductPage, ProductUnavailableError, VariantSelection
from utils.evidence import attach_screenshot

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class AddedItem:
    """Evidence recorded for one successfully added product."""

    url: str
    variants: tuple[VariantSelection, ...]


class ShoppingFlow:
    """Coordinate product pages while preserving the search-page starting point."""

    def __init__(
        self,
        page: Page,
        rng: random.Random,
        capture_screenshot: Callable[[str], None],
    ) -> None:
        self.page = page
        self.rng = rng
        self.capture_screenshot = capture_screenshot
        self.error_page = EbayErrorPage(page)
        self.product_page = ProductPage(page)

    def accepts_cart_candidate(self, url: str) -> bool:
        """Inspect a candidate in a temporary tab without disturbing search results."""
        candidate_page = self.page.context.new_page()
        try:
            response = candidate_page.goto(url, wait_until="domcontentloaded")
            self._require_successful_navigation(response, url)
            if EbayErrorPage(candidate_page).is_displayed():
                raise EbayNavigationError(f"eBay returned its error page while checking {url!r}")
            product_page = ProductPage(candidate_page)
            if product_page.has_add_to_cart():
                return True
            LOGGER.warning("Excluded search candidate without Add to cart: %s", url)
            item_id = urlsplit(url).path.rstrip("/").rsplit("/", 1)[-1]
            attach_screenshot(
                candidate_page,
                f"candidate-{item_id}-without-add-to-cart",
                region=product_page.purchase_actions,
                reason="Candidate excluded: Add to cart did not become visible before timeout.",
            )
            return False
        finally:
            candidate_page.close()

    def add_items_to_cart(
        self,
        urls: Sequence[str],
    ) -> list[AddedItem]:
        """Open every supplied eBay product URL and add it to the cart."""
        self._validate_product_urls(urls)

        search_url = self.page.url
        added_items: list[AddedItem] = []

        for item_number, url in enumerate(urls, start=1):
            self._open_product(url)
            try:
                self.product_page.require_available_listing()
                variants = self.product_page.select_available_variants(self.rng)
                self.product_page.add_to_cart()
            except ProductUnavailableError:
                LOGGER.error(
                    "Required item %d/%d is unavailable: %s",
                    item_number,
                    len(urls),
                    url,
                )
                self.capture_screenshot(f"unavailable-item-{item_number}")
                raise

            added_item = AddedItem(url=url, variants=variants)
            added_items.append(added_item)
            LOGGER.info(
                "Added item %d/%d: %s; variants=%s",
                item_number,
                len(urls),
                url,
                self._format_variants(variants),
            )
            self.capture_screenshot(f"added-item-{item_number}")
            self._return_to_search(search_url)
        return added_items

    @staticmethod
    def _validate_product_urls(urls: Sequence[str]) -> None:
        if not urls:
            raise ValueError("add_items_to_cart requires at least one product URL")

        for url in urls:
            if not isinstance(url, str) or not url.strip():
                raise ValueError("Each product URL must be a non-empty string")
            parsed_url = urlsplit(url)
            if parsed_url.scheme != "https" or parsed_url.hostname != "www.ebay.com":
                raise ValueError("Each product URL must be an HTTPS www.ebay.com URL")

    def _open_product(self, url: str) -> None:
        response = self.page.goto(url, wait_until="domcontentloaded")
        if self.error_page.go_to_home_if_displayed():
            LOGGER.warning("eBay returned its error page while opening %s; retrying once", url)
            response = self.page.goto(url, wait_until="domcontentloaded")
            if self.error_page.is_displayed():
                raise EbayNavigationError(
                    f"eBay returned its error page again while opening {url!r}"
                )
        self._require_successful_navigation(response, url)

    def _return_to_search(self, search_url: str) -> None:
        response = self.page.goto(search_url, wait_until="domcontentloaded")
        if self.error_page.go_to_home_if_displayed():
            # The item is already confirmed in the cart. Continue from Home instead of
            # repeating the Add to cart action or retrying the failing results URL.
            LOGGER.warning(
                "eBay returned its error page while returning to search; continuing from Home"
            )
            return
        self._require_successful_navigation(response, search_url)

    @staticmethod
    def _require_successful_navigation(response: Response | None, url: str) -> None:
        if response is None:
            raise EbayNavigationError(f"No document response while opening {url!r}")
        if not response.ok:
            raise EbayNavigationError(
                f"eBay returned HTTP {response.status} while opening {response.url}"
            )

    @staticmethod
    def _format_variants(variants: tuple[VariantSelection, ...]) -> str:
        if not variants:
            return "none"
        return ", ".join(f"{variant.name}={variant.value}" for variant in variants)
