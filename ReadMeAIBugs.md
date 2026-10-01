# Bug review: supplied search test

Source: the Python screenshot in the [assignment](docs/assignment/automation-developer-assignment.docx).

## 1. Browser setup and cleanup belong in fixtures

Affected lines:

```python
browser = sync_playwright().start().chromium.launch()
page = browser.new_page()
# ... test actions ...
browser.close()
```

The test mixes browser lifecycle with scenario behavior. Repeating this setup across tests
creates duplication. More seriously, an exception before `browser.close()` skips cleanup,
and the Playwright instance started with `.start()` is not explicitly stopped.

Correction: use pytest-playwright's `browser`, `context`, and `page` fixtures. They own setup
and teardown, including cleanup after a failed test. The test receives `page` as a parameter
and contains no manual launch or close. Custom lifecycle fixtures, if needed, should use
`yield` with cleanup in `finally`; this project already uses the official plugin lifecycle.
Browser creation and closing are treated as one issue, not two separate findings.

## 2. Fixed sleeps make the test unreliable and slow

Affected lines:

```python
time.sleep(2)
time.sleep(3)
```

Two seconds do not establish that the search control is ready, and three seconds do not
establish that results have arrived. A slow response can exceed either delay; a fast response
still pays the full delay. These waits depend on timing instead of application state.

Correction: remove both sleeps. Playwright's `fill()` and `click()` wait for their required
actionability conditions. After submitting the query, use a retrying assertion for the
expected result state. In the example below, the query is assumed to return at least one
visible result; a zero-result scenario would need its own expected state.

## 3. Page locators and interactions are embedded in the test

Affected lines:

```python
page.goto("https://example.com")
search_box = page.locator("#search")
search_box.fill("playwright testing")
page.locator(".button").click()
results = page.locator(".result-item")
```

This is a maintenance and POM issue, not proof that every locator is invalid. The test knows
the page's markup and how to operate its controls. A UI change would require editing each
test that repeats these details.

Correction: put locators and page actions in a SearchPage object. Keep the scenario and
assertions in the test. Page-specific navigation can be an `open()` method; a fixture may
call it when navigation is shared setup. A `goto()` inside a test is not inherently a bug.
Moving only selector strings to another file would not fully separate these responsibilities.

## Proposed correction

Illustrative only: the URL and selectors are retained from the supplied example and have
not been verified against a real search application. This snippet was not executed and is
not an additional repository test. In an implementation, the class and test belong in their
respective page-object and test modules; pytest-playwright supplies the `page` fixture.

```python
from playwright.sync_api import Page, expect


class SearchPage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.search_box = page.locator("#search")
        self.search_button = page.locator(".button")
        self.results = page.locator(".result-item")

    def open(self) -> None:
        self.page.goto("https://example.com")

    def search(self, query: str) -> None:
        self.search_box.fill(query)
        self.search_button.click()


def test_search_functionality(page: Page) -> None:
    search_page = SearchPage(page)
    search_page.open()
    search_page.search("playwright testing")
    expect(search_page.results.first).to_be_visible()
```

The synchronous API is valid for pytest. Importing `Page` adds a type annotation; it is not
a replacement for `sync_playwright`, and its absence alone is not a bug. The fixture plugin
owns Playwright startup in the proposed correction.
