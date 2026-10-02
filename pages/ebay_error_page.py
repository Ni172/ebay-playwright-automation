"""Interactions for eBay's known recoverable error page."""

from playwright.sync_api import Locator, Page


class EbayErrorPage:
    """Recognize the known eBay error page and return through its Home control."""

    MESSAGE = "Something went wrong on our end"
    _ERROR_INFO_SELECTOR = "#error-info"
    _HOME_LINK_SELECTOR = '.status--container a.fake-btn[href="https://www.ebay.com"]'

    def __init__(self, page: Page) -> None:
        self.page = page

    @property
    def message(self) -> Locator:
        """Return the known error message inside eBay's error information region."""
        return self.page.locator(self._ERROR_INFO_SELECTOR).filter(has_text=self.MESSAGE)

    @property
    def go_to_home_control(self) -> Locator:
        """Return the error page's stable Home link."""
        return self.page.locator(self._HOME_LINK_SELECTOR)

    def is_displayed(self) -> bool:
        """Return whether the known error message is visible."""
        return self.message.is_visible()

    def go_to_home_if_displayed(self) -> bool:
        """Click the error page's visible Home control when available."""
        if not self.is_displayed():
            return False

        if not self.go_to_home_control.is_visible():
            return False

        self.go_to_home_control.click()
        self.page.wait_for_load_state("domcontentloaded")
        return True
