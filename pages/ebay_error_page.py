"""Interactions for eBay's known recoverable error page."""

from urllib.parse import urlsplit

from playwright.sync_api import Locator, Page, TimeoutError


class EbayRecoveryError(RuntimeError):
    """Raised when returning Home is blocked or never becomes ready."""


class EbayErrorPage:
    """Recognize the known eBay error page and return to the configured Home."""

    MESSAGE = "Something went wrong on our end"
    _ERROR_INFO_SELECTOR = "#error-info"
    _HOME_LINK_SELECTOR = ".status--container a.fake-btn"
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
        return self.page.locator(self._HOME_LINK_SELECTOR).filter(has_text="Go to homepage")

    def is_displayed(self) -> bool:
        """Return whether the known error message is visible."""
        return self.message.is_visible()

    def go_to_home_if_displayed(self) -> bool:
        """Open the configured Home when the error page offers its Home control."""
        if not self.is_displayed():
            return False

        if not self.go_to_home_control.is_visible():
            return False

        # Relative navigation returns to the browser context's configured home URL.
        self.page.goto("/", wait_until="domcontentloaded")
        self._wait_for_home_or_challenge()
        return True

    def _wait_for_home_or_challenge(self) -> None:
        """Wait for Home's search field and report verification blocks."""
        try:
            self.page.locator(self._HOME_SEARCH_SELECTOR).wait_for(
                state="visible",
                timeout=self._HOME_READY_TIMEOUT_MS,
            )
        except TimeoutError as exc:
            if urlsplit(self.page.url).path.startswith(self._CHALLENGE_PATH):
                raise EbayRecoveryError(
                    f"eBay verification blocked Home recovery; URL: {self.page.url}"
                ) from exc
            raise EbayRecoveryError(
                f"Home search field was not visible within {self._HOME_READY_TIMEOUT_MS} ms; "
                f"URL: {self.page.url}"
            ) from exc
        if urlsplit(self.page.url).path != "/" or self.is_displayed():
            raise EbayRecoveryError(
                f"Home recovery did not reach a ready homepage; URL: {self.page.url}"
            )
