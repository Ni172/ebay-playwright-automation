"""Interactions for eBay's known recoverable error page."""

from playwright.sync_api import Page


class EbayErrorPage:
    """Recognize the known eBay error page and return through its Home control."""

    MESSAGE = "Something went wrong on our end"
    _GO_TO_HOMEPAGE_NAME = "Go to homepage"

    def __init__(self, page: Page) -> None:
        self.page = page

    def is_displayed(self) -> bool:
        """Return whether the known error message is visible."""
        return self.page.get_by_text(self.MESSAGE, exact=True).is_visible()

    def go_to_home_if_displayed(self) -> bool:
        """Click the error page's visible Home control when available."""
        if not self.is_displayed():
            return False

        homepage_link = self.page.get_by_role(
            "link",
            name=self._GO_TO_HOMEPAGE_NAME,
            exact=True,
        )
        homepage_button = self.page.get_by_role(
            "button",
            name=self._GO_TO_HOMEPAGE_NAME,
            exact=True,
        )
        homepage_control = homepage_link.or_(homepage_button).first
        if not homepage_control.is_visible():
            return False

        homepage_control.click()
        self.page.wait_for_load_state("domcontentloaded")
        return True
