import hashlib
import random
from collections.abc import Callable, Iterator
from pathlib import Path

import allure
import pytest
from dotenv import load_dotenv
from playwright.sync_api import BrowserContext, Page

from config.settings import ROOT, Settings
from utils.data_loader import (
    load_invalid_cart_cases,
    load_invalid_search_cases,
    load_search_cases,
)
from utils.evidence import attach_screenshot, finish_trace

# Keep each test's outcomes until its context is ready for cleanup.
REPORTS = pytest.StashKey[dict[str, pytest.TestReport]]()


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--case-file", default=str(ROOT / "data/search_cases.json"))
    parser.addoption("--cart-case-file", default=str(ROOT / "data/cart_cases.json"))
    parser.addoption(
        "--negative-case-file",
        default=str(ROOT / "data/search_negative_cases.json"),
    )
    parser.addoption(
        "--invalid-cart-case-file",
        default=str(ROOT / "data/cart_negative_cases.json"),
    )


def pytest_configure(config: pytest.Config) -> None:
    # Real environment variables take precedence over local .env values.
    load_dotenv(ROOT / ".env", override=False)
    if config.getoption("tracing") != "off":
        raise pytest.UsageError("Use EBAY_TRACE, not --tracing; project fixtures own tracing")


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    case_sources = {
        "search_case": ("--case-file", load_search_cases),
        "cart_case": ("--cart-case-file", load_search_cases),
        "negative_search_case": ("--negative-case-file", load_invalid_search_cases),
        "invalid_cart_case": ("--invalid-cart-case-file", load_invalid_cart_cases),
    }
    fixture_name = next(
        (name for name in case_sources if name in metafunc.fixturenames),
        None,
    )
    if fixture_name is None:
        return

    option_name, loader = case_sources[fixture_name]
    case_file = Path(metafunc.config.getoption(option_name))
    cases = loader(case_file)
    case_ids = [case.id for case in cases]
    metafunc.parametrize(fixture_name, cases, ids=case_ids)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    # Let pytest build the report before reading its outcome.
    outcome = yield
    report = outcome.get_result()
    item.stash.setdefault(REPORTS, {})[report.when] = report
    # Capture evidence before fixture teardown closes the page.
    if report.failed and report.when in {"setup", "call"}:
        page = getattr(item, "funcargs", {}).get("page")
        if page is not None:
            attach_screenshot(page, f"{report.when}-failure")


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings.from_env()


@pytest.fixture(scope="session")
def browser_type_launch_args(
    browser_type_launch_args: dict,
    browser_name: str,
) -> dict:
    launch_args = dict(browser_type_launch_args)
    if browser_name == "chromium":
        launch_args["args"] = [*launch_args.get("args", []), "--start-maximized"]
    return launch_args


@pytest.fixture(scope="session")
def browser_context_args(
    browser_context_args: dict,
    settings: Settings,
) -> dict:
    return {
        **browser_context_args,
        "base_url": browser_context_args.get("base_url") or settings.base_url,
        "locale": settings.locale,
        "no_viewport": True,
    }


@pytest.fixture
def context(
    context: BrowserContext, settings: Settings, request: pytest.FixtureRequest, tmp_path: Path
) -> Iterator[BrowserContext]:
    """Extend the official isolated context; let its fixture own close/cleanup."""
    context.set_default_timeout(settings.timeout_ms)
    context.set_default_navigation_timeout(settings.navigation_timeout_ms)
    trace_enabled = settings.trace != "off"
    if trace_enabled:
        context.tracing.start(screenshots=True, snapshots=True, sources=True)

    yield context

    if not trace_enabled:
        return

    reports = request.node.stash.get(REPORTS, {})
    test_failed = any(report.failed for report in reports.values())
    keep_trace = settings.trace == "on" or test_failed
    # The underlying plugin closes the context after this fixture finishes.
    finish_trace(context, tmp_path / "trace.zip", keep_trace=keep_trace)


@pytest.fixture
def rng(settings: Settings, request: pytest.FixtureRequest) -> random.Random:
    # Unlike Python's hash(), SHA-256 stays stable between processes.
    digest = hashlib.sha256(request.node.nodeid.encode()).digest()
    test_seed_offset = int.from_bytes(digest[:8], "big")
    seed = settings.random_seed + test_seed_offset
    allure.dynamic.parameter("random_seed", seed)
    return random.Random(seed)


@pytest.fixture
def screenshot(page: Page) -> Callable[[str], None]:
    """Attach visible item, search, and cart checkpoints to Allure."""

    def capture(name: str) -> None:
        attach_screenshot(page, name)

    return capture
