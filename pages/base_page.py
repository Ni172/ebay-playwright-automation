"""Small shared browser navigation behavior for eBay page objects."""

from playwright.sync_api import Page, Response


class EbayNavigationError(RuntimeError):
    """Raised when eBay does not return a successful document response."""


class BasePage:
    """Base class only for shared page access and document navigation."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def open(self, path: str) -> Response:
        """Navigate to a relative eBay path and stop on an HTTP access error."""
        response = self.page.goto(path, wait_until="domcontentloaded")
        if response is None:
            raise EbayNavigationError(f"No document response while opening {path!r}")
        if not response.ok:
            raise EbayNavigationError(
                f"eBay returned HTTP {response.status} while opening {self.page.url}"
            )
        return response
