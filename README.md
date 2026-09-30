# eBay Playwright Automation

Python end-to-end automation assignment for searching eBay products by price, adding eligible items to the cart, and verifying the cart amount. The planned implementation uses Playwright, pytest, Page Object Model (POM), and Allure.

## Current status

Local infrastructure is implemented: isolated pytest browser fixtures, validated configuration and JSON data, Decimal price parsing, reproducible randomness, screenshots and traces attached to Allure, and local infrastructure checks. Search submission and local XPath extraction of eligible ILS-priced result URLs are implemented; price filtering, live pagination and shopping scenarios are not implemented yet.

Latest local validation: 27 local checks passed and Ruff lint and formatting passed. The live search-submission validation is recorded in the current handoff after its run. Price filtering, live pagination, and shopping functionality are not yet validated.

The latest live search-submission attempt on 2026-09-30 was blocked by eBay with HTTP 403 at the homepage. The Allure report retains the failure screenshot and trace. No retry intended to defeat the block and no bypass was attempted.

## Requirements

- Use Python, Playwright, OOP, and POM. TypeScript signatures in the assignment are examples, not the implementation language.
- Read test inputs from an external JSON file.
- No authentication or credentials are required for the agreed scope.
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

Useful subsets and debugging:

```powershell
python -m pytest -m unit
python -m pytest -m infra --headed
python -m pytest --case-file data/search_cases.json
python -m playwright show-trace artifacts/allure-results/<trace-attachment>.zip
```

`search_case` parametrizes tests from validated JSON; `search_cases` returns the full dataset. `rng` provides a per-test generator with its seed recorded in Allure. `screenshot("checkpoint-name")` attaches evidence. `page` and `context` preserve the plugin's lifecycle and per-test isolation.

Optional `.env` values appear in `.env.example`; actual environment variables take precedence. ILS/en-IL is the agreed configuration because eBay displayed Israeli shekels in the normal local browser context. Other currencies/locales fail explicitly until supported. `--base-url` overrides the environment base URL.

Browser visibility has one project-level control: `--headed` in `pyproject.toml` under
`addopts`. It is currently present, so Chromium opens visibly for every browser test.
Remove only that flag from the same line to run headlessly. This controls browser
visibility only and does not opt in to real eBay tests.

`EBAY_TRACE=on` retains all primary-context traces; `off` disables them; `retain-on-failure` retains setup/call failures known at context teardown. Use default `on` for teardown-only failures too. Do not combine this with `--tracing`. Additional contexts from `new_context` do not receive custom trace wrapping.

Results go to `artifacts/allure-results`, and the report to `artifacts/allure-report`. Results are cleaned at the start of each run; archive evidence first if needed. Failure screenshots are best effort for an open `page` during setup/call failures. Allure's pytest log capture is enabled. The failure-pipeline check intentionally fails a child test in a temporary directory; its enclosing check must pass.

Real-site tests must use the `e2e` marker and require `--run-e2e`. The search-submission test opens eBay, submits one external JSON query, verifies the resulting URL, and attaches a screenshot. If eBay blocks access, the test fails explicitly with retained evidence; it does not attempt a bypass. Local infrastructure checks do not access eBay. There is no CI or GitHub Actions workflow.

## Decisions pending

- Authentication is out of scope. Any future real-account login requires separate approval and credentials supplied outside source control.
- Whether the asserted amount is the items subtotal or a total including delivery and taxes.
- Behavior when a selected variant changes the eligible price or a product cannot be added.
- Empty-cart setup and cleanup, including permission before modifying an existing account cart.
- The zero-result E2E outcome: a valid search result must not silently count as proof of successful add-to-cart behavior.

## GitHub submission

The final deliverable is a repository URL, not just local files. Before submission, the repository should contain the implementation, external test data, verified run instructions, architecture explanation, assumptions and limitations, the bug analysis, and a run report or accessible report artifact. Reviewer access must be verified.

The public repository is available at `https://github.com/Ni172/ebay-playwright-automation`. Credentials, session state, and sensitive screenshots must not be committed.

## Project records

- [Working instructions](AGENTS.md)
- [Current handoff](HANDOFF.md)
- [Architecture](docs/architecture.md)
- [Bug-analysis preparation](ReadMeAIBugs.md)

Source requirements: `C:\Users\ElieBook\Downloads\תרגיל למפתח אוטומציה PM.docx`. The document's assessment weights sum to 110%; this is recorded as an apparent inconsistency, not corrected by assumption.
