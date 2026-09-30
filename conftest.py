import hashlib
import random
from collections.abc import Callable, Iterator
from pathlib import Path

import allure
import pytest
from dotenv import load_dotenv
from playwright.sync_api import BrowserContext, Page

from config.settings import ROOT, Settings
from utils.data_loader import SearchCase, load_search_cases
from utils.evidence import attach_screenshot, finish_trace

# Keep each test's outcomes until its context is ready for cleanup.
REPORTS = pytest.StashKey[dict[str, pytest.TestReport]]()


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--run-e2e", action="store_true", help="Opt in to real-site tests")
    parser.addoption("--case-file", default=str(ROOT / "data/search_cases.json"))


def pytest_configure(config: pytest.Config) -> None:
    # Real environment variables take precedence over local .env values.
    load_dotenv(ROOT / ".env", override=False)
    if config.getoption("tracing") != "off":
        raise pytest.UsageError("Use EBAY_TRACE, not --tracing; project fixtures own tracing")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-e2e"):
        return

    for item in items:
        if item.get_closest_marker("e2e"):
            item.add_marker(pytest.mark.skip(reason="Real-site tests require --run-e2e"))


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "search_case" not in metafunc.fixturenames:
        return

    case_file = Path(metafunc.config.getoption("--case-file"))
    cases = load_search_cases(case_file)
    case_ids = [case.id for case in cases]
    metafunc.parametrize("search_case", cases, ids=case_ids)


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
def browser_context_args(browser_context_args: dict, settings: Settings) -> dict:
    return {
        **browser_context_args,
        "base_url": browser_context_args.get("base_url") or settings.base_url,
        "locale": settings.locale,
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
def search_cases(pytestconfig: pytest.Config) -> tuple[SearchCase, ...]:
    return load_search_cases(Path(pytestconfig.getoption("--case-file")))


@pytest.fixture
def screenshot(page: Page) -> Callable[[str], None]:
    """Explicit checkpoints for item and cart evidence in future page flows."""

    def capture(name: str) -> None:
        attach_screenshot(page, name)

    return capture
