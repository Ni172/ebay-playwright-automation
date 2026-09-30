import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.infra


def test_local_page_and_evidence(page, screenshot, rng):
    page.set_content("<button onclick=\"this.textContent='Ready'\">Start</button>")
    page.get_by_role("button", name="Start").click()
    expect(page.get_by_role("button", name="Ready")).to_be_visible()
    assert rng.choice(["blue", "red"]) in {"blue", "red"}
    screenshot("local-infrastructure-check")


def test_contexts_do_not_share_cookies(context, new_context):
    context.add_cookies([{"name": "isolation", "value": "yes", "url": "https://example.test"}])
    other = new_context()
    assert context.cookies()
    assert other.cookies() == []
