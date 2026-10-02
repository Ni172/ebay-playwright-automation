# eBay Playwright Automation

Local Python E2E tests for eBay: search by price, add five items, and verify the cart Subtotal.
Stack: synchronous Playwright, pytest, Page Object Model (POM), JSON data, Decimal, and Allure 3.

## 1. Install prerequisites (Windows / PowerShell)

Install the missing tools below. Skip a command if that tool is already installed.

```powershell
winget install --id Git.Git --exact --source winget
winget install --id Python.Python.3.13 --exact --source winget
winget install --id Google.Chrome --exact --source winget
winget install --id OpenJS.NodeJS.LTS --exact --source winget --accept-package-agreements --accept-source-agreements
```

Node.js LTS includes **npm and npx**; do not install them separately. Node.js is used only
for Allure reports; the tests remain Python. This Allure 3 setup does not require Java.
If winget is unavailable, use the official installers for [Git](https://git-scm.com/downloads/win),
[Python](https://www.python.org/downloads/windows/), [Chrome](https://www.google.com/chrome/),
and [Node.js LTS](https://nodejs.org/en/download).

Close and reopen PowerShell and your IDE after installation, then verify:

```powershell
git --version
py -3.13 --version
node --version
npm --version
```

## 2. Clone and install project dependencies

```powershell
git clone https://github.com/Ni172/ebay-playwright-automation.git
cd ebay-playwright-automation
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
npm ci --no-audit --no-fund
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
| Search: five results under ILS 220, zero under ILS 0.01, 65 across two pages (60 + 5) | 3 |
| Invalid search inputs rejected before navigation | 10 |
| Search, add all five items, verify cart count and Subtotal | 1 |
| Invalid cart URL lists rejected before navigation | 3 |

Run the full suite (adds five items to an isolated guest cart):

```powershell
.\.venv\Scripts\python.exe -m pytest tests/e2e --browser-channel chrome -vv --log-cli-level=INFO
```

Or run one module / scenario:

```powershell
# Search module: 13 cases; no cart additions
.\.venv\Scripts\python.exe -m pytest tests/e2e/test_search_submission.py --browser-channel chrome -vv
# Cart module: one shopping scenario and three invalid-input cases
.\.venv\Scripts\python.exe -m pytest tests/e2e/test_add_items_to_cart.py --browser-channel chrome -vv
# Only the 65-result pagination scenario
.\.venv\Scripts\python.exe -m pytest tests/e2e/test_search_submission.py -k shoes-pagination-under-220-ils --browser-channel chrome -vv
```

These are real E2E tests by default. Chrome is visible and maximized; `--headed` is in
`pyproject.toml`. Remove that flag there to run headlessly. To use bundled Chromium instead,
run `.\.venv\Scripts\python.exe -m playwright install chromium`, then omit `--browser-channel chrome`.

## 4. Generate and open Allure

After a test run, including a failed run:

```powershell
npm run report
npm run report:open
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
| `pages/` | Page locators and interactions, including XPath search-result extraction |
| `flows/shopping_flow.py` | Visit each product, select available variants, confirm additions |
| `tests/e2e/`, `utils/cart_assertions.py` | Scenario expectations and exact count / budget assertions |
| `conftest.py`, `config/` | Browser fixtures, isolated contexts, configuration, reproducible seeds |
| `data/`, `utils/` | External cases, data validation, Decimal parsing, evidence |

Search and cart data are separate. Override inputs with `--case-file`, `--negative-case-file`,
`--cart-case-file`, or `--invalid-cart-case-file`. See [architecture](docs/architecture.md).

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
  a guest; an explicit identification function remains pending.
- **Local-only execution and repository contents:** tests are run on the local machine, not through
  CI. Credentials, login/session state, and generated screenshots, traces, and reports are not
  committed to Git.

Verified locally with Python 3.13.9, Node.js 24.19.0, npm 11.17.0, and the locked Allure 3.19.1.
For actual live-run outcomes, see [HANDOFF.md](HANDOFF.md); the suite is not currently all green.

[Assignment](docs/assignment/automation-developer-assignment.docx) ·
[Bug review](ReadMeAIBugs.md) · [Working rules](AGENTS.md) ·
[GitHub repository](https://github.com/Ni172/ebay-playwright-automation)
