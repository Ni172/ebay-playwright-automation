import logging
from pathlib import Path

import allure
from playwright.sync_api import BrowserContext, Error, Page

LOGGER = logging.getLogger(__name__)


def attach_screenshot(page: Page, name: str) -> None:
    """Best-effort evidence must not replace the original test failure."""
    if page.is_closed():
        return

    try:
        image = page.screenshot(full_page=True, timeout=5_000)
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
