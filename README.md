# eBay Playwright Automation

Python end-to-end automation assignment for searching eBay products by price, adding eligible items to the cart, and verifying the cart amount. The planned implementation uses Playwright, pytest, Page Object Model (POM), and Allure.

The original assignment is retained in [`docs/assignment/automation-developer-assignment.docx`](docs/assignment/automation-developer-assignment.docx).

## Current status

The repository exposes real eBay E2E scenarios plus request-validation cases that fail before navigation. Shared pytest fixtures provide isolated browser contexts, validated JSON data, reproducible randomness, screenshots, traces, and Allure output. Search submission, optional max-price filtering, XPath result extraction, pagination, ProductPage, and ShoppingFlow are implemented. The latest completed full Google Chrome run predates the expanded search matrix; it passed the earlier three scenarios and confirmed exactly five cart additions.

If eBay returns its known `Something went wrong on our end` page, shared navigation uses the visible `Go to homepage` control. Search resubmits the original query once. ShoppingFlow retries a product URL once, while a failure returning to search falls back to Home and continues without repeating the already confirmed Add to cart action. An error before cart confirmation also returns Home but fails without clicking Add to cart again. Repeated errors fail explicitly; recovery never loops or attempts to bypass a block.

Latest validation is recorded in the current handoff. eBay availability is external and can change between runs; a site error is recorded honestly instead of being bypassed.

The live cart scenario requests five eligible products plus up to three reserve candidates. ShoppingFlow replaces only listings that eBay explicitly marks ended or unavailable, with a warning and screenshot. It still requires exactly five confirmed additions and fails if the reserve pool is exhausted; other product or cart errors are never skipped.

## Requirements

- Use Python, Playwright, OOP, and POM. TypeScript signatures in the assignment are examples, not the implementation language.
- Read test inputs from an external JSON file.
- Identification is still pending clarification as either a Guest flow or a Login Stub. Real credentials are not stored in the repository.
- Search by query and maximum price. Apply the site's price filter when available.
- Collect eligible product URLs using XPath, up to the requested limit (default 5).
- Continue through pagination when necessary, stopping at the limit or when pages end. Returning fewer results, including zero, is valid.
- Open each selected product, choose random available variants when required, add it to the cart, and return to the search page or tab.
- Record a log and screenshot for every successfully added item.
- Verify the agreed cart amount against `budget_per_item * items_count`, and retain cart evidence.
- Produce an Allure report and a separate `ReadMeAIBugs.md` with at least three explained issues and proposed corrections.
- CAPTCHA handling and bypass are out of scope. If a CAPTCHA prevents progress, report the run as blocked with evidence; do not report it as passed.
- Submit a GitHub repository link with access for the reviewer.

## Architecture

See [architecture and diagram](docs/architecture.md) for component responsibilities, proposed file layout, and decisions needed before implementation.

The selected approach is Python with the Playwright synchronous API, the official pytest Playwright plugin, and Allure's pytest integration. Prices will use `Decimal`. The design stays small enough for the assignment's stated 3–4 hours of implementation.

## Running the project

Prerequisites: Python 3.13 (validated locally with 3.13.9) and pip. Node.js LTS with npm generates Allure 3 reports only; automation remains Python. Java is not needed for this Allure 3 setup. Execution is local; GitHub is used to submit the repository link.

### Windows: install Node.js and npm

Install the Node.js LTS package once in an elevated or standard PowerShell session:

```powershell
winget install --id OpenJS.NodeJS.LTS --exact --source winget --accept-package-agreements --accept-source-agreements
```

Close and reopen the terminal (and PyCharm if it was already open), then verify both commands are available:

```powershell
node -v
npm -v
```

npm is included with the Node.js installation; do not install it separately.

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip check
python -m playwright install chromium
python -m pytest
python -m ruff check .
python -m ruff format --check .
npm ci --no-audit --no-fund
npm run report
npm run report:open
```

Use a Python 3.13 interpreter for the environment creation command. If PowerShell blocks activation, use `.\.venv\Scripts\python.exe` instead of `python` for subsequent commands; no execution-policy change is required.

Python dependencies, including indirect dependencies, are pinned in `requirements.txt`. `pyproject.toml` contains only pytest and Ruff configuration. When changing a dependency, resolve and verify the complete set of pins together.

Reporting dependencies remain locked in `package-lock.json`. `npm ci` installs them locally into `node_modules`; it is not a CI pipeline. This workstation uses the system Node.js LTS installation and the standard `npm` command.

Live scenarios and debugging:

```powershell
python -m pytest tests/e2e --run-e2e --browser-channel chrome -vv
python -m pytest tests/e2e/test_search_submission.py --run-e2e --browser-channel chrome -vv
python -m pytest tests/e2e/test_add_items_to_cart.py --run-e2e --browser-channel chrome -vv
python -m playwright show-trace artifacts/allure-results/<trace-attachment>.zip
```

`search_case` parametrizes valid search coverage from `data/search_cases.json`. `negative_search_case` reads invalid inputs and expected errors from `data/search_negative_cases.json`. `cart_case` independently reads `data/cart_cases.json`, so additional search cases do not add more products to the live cart scenario. `search_cases` returns the full valid search dataset. `rng` provides a per-test generator with its seed recorded in Allure. `screenshot("checkpoint-name")` attaches evidence. `page` and `context` preserve the plugin's lifecycle and per-test isolation. Override the datasets with `--case-file`, `--negative-case-file`, and `--cart-case-file` respectively.

Screenshots use a 1920x1080 browser viewport and capture the visible viewport rather than the entire scrollable page. Before capture, the evidence helper waits conditionally for the completed document, loaded fonts, and images intersecting the viewport; animations are disabled during capture. A bounded timeout prevents a stalled external asset from suppressing all evidence. Playwright traces retain the broader debugging context.

Optional `.env` values appear in `.env.example`; actual environment variables take precedence. ILS/en-IL is the agreed configuration because eBay displayed Israeli shekels in the normal local browser context. Other currencies/locales fail explicitly until supported. `--base-url` overrides the environment base URL.

Browser visibility has one project-level control: `--headed` in `pyproject.toml` under
`addopts`. It is currently present, so Chromium opens visibly for every browser test.
Remove only that flag from the same line to run headlessly. This controls browser
visibility only and does not opt in to real eBay tests.

Playwright calls the browser engine `chromium`. The current E2E commands use the installed
Google Chrome binary by adding `--browser-channel chrome`, matching the owner's normal
browser. Browser selection is independent of the known-error recovery implemented in
`EbayErrorPage`.

`EBAY_TRACE=on` retains all primary-context traces; `off` disables them; `retain-on-failure` retains setup/call failures known at context teardown. Use default `on` for teardown-only failures too. Do not combine this with `--tracing`. Additional contexts from `new_context` do not receive custom trace wrapping.

Pytest uses `--capture=tee-sys`, so `print()` output remains visible in the terminal and is also attached to each Allure test as `stdout`. Do not add `-s`, because it disables stdout capture and removes those prints from the report.

Results go to `artifacts/allure-results`, and the report to `artifacts/allure-report`. Results are cleaned at the start of each run; archive evidence first if needed. Failure screenshots are best effort for an open `page` during setup/call failures. Allure's pytest log capture is enabled.

The suite uses the `e2e` marker and requires `--run-e2e`. The external search matrix covers `shoes` at ILS 220, `womens t-shirts` with a valid result containing fewer than five URLs, and a 121-result `t-shirts` case that must visit exactly three distinct result pages. The pagination case records and prints each page URL and the number of unique eligible URLs it contributed, proving that the earlier pages did not satisfy the requested limit before `Next` was used. Search attempts eBay's visible max-price filter when present, collects XPath result cards, follows an enabled Next link until it reaches the requested limit or the pages end, and rechecks every displayed price locally. Externally supplied negative cases in the same E2E module reject blank queries, invalid prices, and invalid limits before navigation. If eBay blocks access, a live scenario stops explicitly with retained evidence; it does not attempt a bypass. There is no CI or GitHub Actions workflow.

## Decisions pending

- Authentication is out of scope. Any future real-account login requires separate approval and credentials supplied outside source control.
- Whether the asserted amount is the items subtotal or a total including delivery and taxes.
- Behavior when a selected variant changes the eligible price or a product cannot be added.
- Empty-cart setup and cleanup, including permission before modifying an existing account cart.
- The live stability of the new fewer-than-five and forced-pagination search cases must be confirmed against eBay before their thresholds are treated as final evidence.

## GitHub submission

The final deliverable is a repository URL, not just local files. Before submission, the repository should contain the implementation, external test data, verified run instructions, architecture explanation, assumptions and limitations, the bug analysis, and a run report or accessible report artifact. Reviewer access must be verified.

The public repository is available at `https://github.com/Ni172/ebay-playwright-automation`. Credentials, session state, and sensitive screenshots must not be committed.

## Project records

- [Working instructions](AGENTS.md)
- [Current handoff](HANDOFF.md)
- [Architecture](docs/architecture.md)
- [Bug-analysis preparation](ReadMeAIBugs.md)

The unchanged source assignment is retained at [`docs/assignment/automation-developer-assignment.docx`](docs/assignment/automation-developer-assignment.docx). Its assessment weights sum to 110%; this is recorded as an apparent inconsistency, not corrected by assumption.
