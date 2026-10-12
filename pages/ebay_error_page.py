"""Interactions for eBay's known recoverable error page."""

from playwright.sync_api import Locator, Page, TimeoutError


class EbayRecoveryError(RuntimeError):
    """Raised when returning Home is blocked or never becomes ready."""


class EbayErrorPage:
    """Recognize the known eBay error page and return through its Home control."""

    MESSAGE = "Something went wrong on our end"
    _ERROR_INFO_SELECTOR = "#error-info"
    _HOME_LINK_SELECTOR = '.status--container a.fake-btn[href="https://www.ebay.com"]'
    _HOME_SEARCH_SELECTOR = 'input[placeholder="Search for anything"]'
    _CHALLENGE_PATH = "/splashui/challenge"
    _HOME_READY_TIMEOUT_MS = 30_000

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
        self._wait_for_home_or_challenge()
        return True

    def _wait_for_home_or_challenge(self) -> None:
        """Require a ready Home page before callers retry their operation."""
        try:
            outcome = self.page.wait_for_function(
                """
                ({ searchSelector, challengePath }) => {
                    if (location.pathname.startsWith(challengePath)) return 'challenge';
                    if (location.hostname !== 'www.ebay.com' || location.pathname !== '/') {
                        return false;
                    }
                    const input = document.querySelector(searchSelector);
                    if (!input || input.disabled || input.readOnly) return false;
                    const bounds = input.getBoundingClientRect();
                    const style = getComputedStyle(input);
                    return bounds.width > 0 && bounds.height > 0
                        && style.visibility === 'visible' ? 'home' : false;
                }
                """,
                arg={
                    "searchSelector": self._HOME_SEARCH_SELECTOR,
                    "challengePath": self._CHALLENGE_PATH,
                },
                timeout=self._HOME_READY_TIMEOUT_MS,
            )
        except TimeoutError as exc:
            raise EbayRecoveryError(
                f"Home did not show an available search field within "
                f"{self._HOME_READY_TIMEOUT_MS} ms after Go to homepage; URL: {self.page.url}"
            ) from exc
        if outcome.json_value() == "challenge":
            raise EbayRecoveryError(
                f"eBay verification blocked Home recovery; no retry attempted. URL: {self.page.url}"
            )
