# Project handoff

Updated: 2026-10-01 (Asia/Jerusalem).

## Current scope

The repository contains three real eBay E2E scenarios in two files:

- search submission;
- search by name and maximum price;
- search, random available variant selection, and exactly five confirmed cart additions.

The project uses Python, Playwright synchronous API, pytest, POM, external JSON data, Decimal money values, reproducible randomness, and Allure. Execution is local through Google Chrome for real eBay scenarios. Publication of the current working tree is approved and pending final verification, commit, and push.

## Implemented

- SearchResultsPage submits the external query, uses the visible price filter when available, extracts result URLs with XPath, validates displayed ILS prices, and follows enabled pagination.
- ProductPage uses semantic Playwright locators and short CSS selectors without regular expressions. It chooses random enabled values from native selects and button listboxes and records the selected labels.
- ShoppingFlow coordinates product navigation, cart confirmation, screenshots, reserve candidates for explicitly unavailable listings, and the exact required item count.
- EbayErrorPage separately recognizes `Something went wrong on our end` and clicks the exact `Go to homepage` link or button. Search recovery is bounded to one retry.
- Every pytest browser context is isolated. Evidence fixtures attach screenshots and traces to Allure.

## Current E2E evidence

On 2026-10-01, the final cleaned E2E suite ran through installed Google Chrome. It collected exactly three tests and all three passed in 153.91 seconds. The shopping scenario collected eight eligible `shoes` candidates at or below ILS 220 and confirmed exactly five cart additions. The reproducible selection included `US Shoes Size=Men 10.5`. Known eBay error pages encountered while returning to search recovered through Home without repeating confirmed additions. A preceding run had two passes and one external eBay search-error failure; its results were replaced by the final clean run rather than mixed into the report.

Allure was regenerated from this run. `artifacts/allure-results` contains exactly three result files, all with status `passed` and all with captured `stdout`. Its seven screenshots are 1920x1080, and `artifacts/allure-report/index.html` exists. No earlier test results are included.

## Verification commands

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m pytest tests\e2e --run-e2e --browser-channel chrome -vv --log-cli-level=INFO
npm run report
npm run report:open
```

## Remaining assignment work

- Decide and implement the required identification function as a documented Guest or Login Stub behavior.
- Implement CartPage and `assert_cart_total_not_exceeds` after agreeing whether the asserted amount is subtotal or delivered total.
- Agree how to handle a selected variant that changes the displayed item price.
- Complete `ReadMeAIBugs.md` without claiming that an assisted review satisfied the assignment's unaided-review condition.

CAPTCHA solving, stealth changes, and attempts to defeat eBay blocking are out of scope. Credentials, authentication state, and sensitive evidence must not be committed.

Pytest is configured with `--capture=tee-sys`. Prints appear in the terminal and are attached to Allure as `stdout`. Using `-s` disables that capture and must be avoided when generating report evidence.

Allure screenshots now use a fixed 1920x1080 viewport and `full_page=False`. Earlier full-page eBay screenshots reached heights above 13,000 pixels, causing Allure to shrink the entire page into an unreadable preview. The viewport capture preserves a normal 16:9 view while Playwright trace remains available for full debugging context.

Before each screenshot, the evidence helper conditionally waits up to ten seconds for document completion, loaded fonts, and every image currently intersecting the viewport to finish loading. Screenshot animations are disabled. If an external asset stalls, the helper logs a warning and still captures evidence instead of replacing the test outcome.

## Source

The original assignment is retained unchanged at `docs/assignment/automation-developer-assignment.docx`.
