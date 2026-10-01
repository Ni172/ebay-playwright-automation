import logging
from pathlib import Path

import allure
from playwright.sync_api import BrowserContext, Error, Page, TimeoutError

LOGGER = logging.getLogger(__name__)


def _wait_for_visible_content(page: Page) -> None:
    """Wait for the document, fonts, and viewport images without fixed sleeps."""
    try:
        page.wait_for_function(
            """
            () => {
                const fontsReady = !document.fonts || document.fonts.status === 'loaded';
                const visibleImagesReady = [...document.images].every(image => {
                    const bounds = image.getBoundingClientRect();
                    const isInViewport = bounds.bottom > 0
                        && bounds.right > 0
                        && bounds.top < window.innerHeight
                        && bounds.left < window.innerWidth;
                    return !isInViewport || image.complete;
                });
                return document.readyState === 'complete'
                    && fontsReady
                    && visibleImagesReady;
            }
            """,
            timeout=10_000,
        )
    except TimeoutError:
        # Evidence is still more useful than no screenshot when an external asset stalls.
        LOGGER.warning("Viewport content did not finish loading before the screenshot timeout")


def attach_screenshot(page: Page, name: str) -> None:
    """Best-effort evidence must not replace the original test failure."""
    if page.is_closed():
        return

    try:
        _wait_for_visible_content(page)
        # A viewport image stays readable in Allure. Full-page images from eBay can be
        # over 10,000 px tall, so Allure shrinks their content into a tiny preview.
        image = page.screenshot(
            full_page=False,
            animations="disabled",
            timeout=15_000,
        )
        allure.attach(image, name=name, attachment_type=allure.attachment_type.PNG)
    except Error:
        LOGGER.warning("Could not capture screenshot %s", name, exc_info=True)


def finish_trace(context: BrowserContext, path: Path, *, keep_trace: bool) -> None:
    """Stop recording and attach retained evidence without hiding a test failure."""
    try:
        if not keep_trace:
            context.tracing.stop()
            return

        context.tracing.stop(path=path)
        allure.attach.file(
            str(path),
            name="playwright-trace",
            extension="zip",
            attachment_type="application/zip",
        )
    except Error:
        LOGGER.warning("Could not finish Playwright trace", exc_info=True)
