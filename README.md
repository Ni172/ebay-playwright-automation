# eBay Playwright Automation

Local Python E2E tests for eBay using synchronous Playwright, pytest, Page Object Model (POM),
external JSON data, `Decimal`, and Allure 3.

The repository implements the assignment's four central responsibilities:

- identify the fresh browser session as an eBay Guest;
- search by name and price, using pagination when the requested limit exceeds one page;
- add every returned product, selecting available variants with a reproducible random seed;
- verify the exact cart item count and the displayed Subtotal against the full budget.

## 1. Install prerequisites (Windows / PowerShell)

Install the missing tools below. Skip a command if that tool is already installed.

```powershell
winget install --id Git.Git --exact --source winget
winget install --id Python.Python.3.13 --exact --source winget
winget install --id Google.Chrome --exact --source winget
winget install --id OpenJS.NodeJS.LTS --exact --source winget --accept-package-agreements --accept-source-agreements
```

Node.js LTS includes **npm**; do not install it separately. Node.js is used only
for Allure reports; the tests remain Python. This Allure 3 setup does not require Java.
If winget is unavailable, use the official installers for [Git](https://git-scm.com/downloads/win),
[Python](https://www.python.org/downloads/windows/), [Chrome](https://www.google.com/chrome/),
and [Node.js LTS](https://nodejs.org/en/download).

Close and reopen PowerShell and your IDE after installation, then verify:

```powershell
git --version
py -3.13 --version
node --version
npm.cmd --version
```

## 2. Clone and install project dependencies

```powershell
git clone https://github.com/Ni172/ebay-playwright-automation.git
cd ebay-playwright-automation
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
npm.cmd ci --no-audit --no-fund
```

If you already have the repository, start in its root and skip cloning.
All commands below run from that directory. They use the virtual environment directly,
so activation is optional. Python dependencies are pinned in `requirements.txt`;
`npm ci` installs the Allure version locked in `package-lock.json` into `node_modules`.
No global Allure installation is needed. Keep both dependency files in the checkout.

## 3. Check and run tests

Check the installation without contacting eBay:

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m pytest --collect-only --browser-channel chrome -q --alluredir=artifacts/collection-check
```

Collection should list **17 cases**:

| Coverage | Cases |
| --- | ---: |
| **Main E2E: search, add all five items, verify cart count and Subtotal** | **1** |
| Search: five results under ILS 220, zero under ILS 0.01, 65 across two pages (60 + 5) | 3 |
| Invalid search inputs rejected before navigation | 10 |
| Invalid cart URL lists rejected before navigation | 3 |

### Run the main E2E test (recommended)

This is the core assignment scenario: it searches, adds all five returned items to a fresh guest
cart, verifies the exact cart count, and reads the displayed Subtotal.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/e2e/test_add_items_to_cart.py::test_searches_and_adds_every_eligible_item --browser-channel chrome -vv
```

This command contacts live eBay. It may correctly fail the budget assertion when eBay shipping
makes the displayed Subtotal exceed ILS 1,100.00; that result still proves the full cart flow ran.

### Run the full suite (when needed)

eBay can intermittently show its external **eBay error page** during search, filtering,
pagination, or product navigation. Prefer the main E2E test above for a focused verification of
the assignment's central flow. Use the full suite when you specifically need its broader search
and input-validation coverage:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/e2e --browser-channel chrome -vv --log-cli-level=INFO
```

The shopping scenario changes only its fresh guest context by adding five items to that context's
cart; it does not sign in or complete a purchase.

Or run one module / scenario:

```powershell
# Search module: 13 cases; no cart additions
.\.venv\Scripts\python.exe -m pytest tests/e2e/test_search_submission.py --browser-channel chrome -vv
# Cart module: the main shopping scenario and three invalid-input cases
.\.venv\Scripts\python.exe -m pytest tests/e2e/test_add_items_to_cart.py --browser-channel chrome -vv
# Only the 65-result pagination scenario
.\.venv\Scripts\python.exe -m pytest tests/e2e/test_search_submission.py -k shoes-pagination-under-220-ils --browser-channel chrome -vv
```

These are real E2E tests by default. Chrome is visible and maximized; `--headed` is in
`pyproject.toml`. To use bundled Chromium instead, run
`.\.venv\Scripts\python.exe -m playwright install chromium`, then omit `--browser-channel chrome`.

### Run headlessly

The default configuration runs Chrome visibly. To run the main E2E scenario headlessly, override
the configured `--headed` option:

```powershell
python -m pytest -o addopts="" tests\e2e\test_add_items_to_cart.py::test_searches_and_adds_every_eligible_item --browser-channel chrome -vv -ra --strict-markers --capture=tee-sys --clean-alluredir --alluredir=artifacts\allure-headless-results
```

Headless mode does not bypass CAPTCHA and may still be blocked by eBay.

## 4. Generate and open Allure

After a test run, including a failed run:

```powershell
npm.cmd run report
npm.cmd run report:open
```

Results are in `artifacts/allure-results`; the generated report is in `artifacts/allure-report`.
Open the report through the command above, not by double-clicking `index.html`.
Keep that terminal open while viewing; press **Ctrl+C** to stop the report server.
`npm run report` replaces the generated default report. Each pytest run cleans its selected
Allure results directory, so the default report describes the latest run, not all earlier runs.

To preserve raw results from a separate run, use a new directory name:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/e2e --browser-channel chrome -vv --alluredir=artifacts/allure-my-run
```

Allure includes logs, captured stdout, random seeds, screenshots, and trace attachments.
Keep `--capture=tee-sys`; adding `-s` removes stdout from the report. To inspect the first
trace from the default results directory:

```powershell
$trace = Get-ChildItem artifacts/allure-results -Filter *.zip | Select-Object -First 1
.\.venv\Scripts\python.exe -m playwright show-trace $trace.FullName
```

## Configuration and architecture

Optional settings are listed in `.env.example`; copy it to `.env` only if you need overrides.
Real environment variables take precedence. Defaults: ILS / en-IL, action timeout 10 seconds,
navigation timeout 30 seconds, and `EBAY_TRACE=on`. Do not also enable plugin `--tracing`.

| Location | Responsibility |
| --- | --- |
| `pages/` | Guest identification and page interactions, including XPath result extraction |
| `flows/shopping_flow.py` | Visit each product, select available variants, confirm additions |
| `tests/e2e/`, `utils/cart_assertions.py` | Scenario expectations and exact count / budget assertions |
| `conftest.py`, `config/` | Browser fixtures, isolated contexts, configuration, reproducible seeds |
| `data/`, `utils/` | External cases, data validation, Decimal parsing, evidence |

Search and cart data are separate. Override inputs with `--case-file`, `--negative-case-file`,
`--cart-case-file`, or `--invalid-cart-case-file`. See [architecture](docs/architecture.md).

Page objects keep selectors as named constants and expose reusable locator properties. Use CSS or
XPath—whichever is clearer and more reliable—with stable attributes such as `data-testid`,
`data-test-id`, IDs, and ARIA state. XPath is required for search-result extraction by the assignment.

### Key pytest fixtures

| Fixture | Responsibility |
| --- | --- |
| `settings` | Loads validated project settings from environment variables and `.env`. |
| `browser_type_launch_args` | Applies Chromium launch arguments, including maximized browser startup. |
| `browser_context_args` | Configures each fresh context with the eBay base URL, locale, and native viewport. |
| `context` | Sets timeouts and starts/stops Playwright tracing. The underlying `pytest-playwright` fixture owns context cleanup; closing the context also closes its pages. |
| `rng` | Creates a reproducible random generator per test and records its seed in Allure. |
| `screenshot` | Attaches named screenshots to the Allure report. |

## Verified local results

The local non-live verification passes `pip check`, Ruff lint and format, and collection of all
17 E2E cases. No mocked, simulated, or additional test layer is included.

One full-suite run and one execution of the core shopping scenario were blocked by eBay CAPTCHA.
The resulting Allure evidence records the blocked executions honestly; CAPTCHA solving or bypass
is out of scope.

## Troubleshooting and current limits

- **eBay error page, CAPTCHA, or unavailable listing:** this is the main source of live-run
  instability. eBay can return its `Something went wrong on our end` page after a
  search, price filtering, pagination, or opening a product. When its visible **Go to homepage**
  control is available, the test returns Home and retries the original search or product URL once.
  If the same error occurs again, the test fails and retains its evidence instead of treating the
  result as empty or silently skipping an item. After an item is already confirmed in the cart, a
  failed return to the search results continues from Home without repeating that addition. CAPTCHA
  solving or bypass is out of scope.
- **Cart budget failure:** eBay's displayed Subtotal includes shipping. Five qualifying items
  can still exceed ILS 1,100; this must fail the assertion. Items are never skipped to make it pass.
- **Fresh guest context:** every test starts with a new browser context: no login, saved cookies,
  cart contents, or session data from another test are reused. The project currently tests eBay as
  a guest, and `identify_as_guest()` requires the signed-out identity region before searching.
- **Local-only execution and repository contents:** tests are run on the local machine, not through
  CI. Credentials, login/session state, and generated screenshots, traces, and reports are not
  committed to Git.

Verified locally with Python 3.13.9, Node.js 24.19.0, npm 11.17.0, and the locked Allure 3.19.1.
The suite is not currently all green because live shipping charges can exceed the required budget.

[Assignment](docs/assignment/automation-developer-assignment.docx) ·
[Bug review](ReadMeAIBugs.md) · [Working rules](AGENTS.md) ·
[GitHub repository](https://github.com/Ni172/ebay-playwright-automation)
