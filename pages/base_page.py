"""Small shared browser navigation behavior for eBay page objects."""

from playwright.sync_api import Page, Response

from pages.ebay_error_page import EbayErrorPage


class EbayNavigationError(RuntimeError):
    """Raised when eBay does not return a successful document response."""


class BasePage:
    """Base class only for shared page access and document navigation."""

    def __init__(self, page: Page) -> None:
        self.page = page
        self.error_page = EbayErrorPage(page)

    def open(self, path: str) -> Response:
        """Navigate and recover through eBay's known homepage error control."""
        response = self.page.goto(path, wait_until="domcontentloaded")
        if response is None:
            raise EbayNavigationError(f"No document response while opening {path!r}")
        if self.error_page.go_to_home_if_displayed():
            return response
        if not response.ok:
            raise EbayNavigationError(
                f"eBay returned HTTP {response.status} while opening {self.page.url}"
            )
        return response
