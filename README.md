# eBay Playwright Automation

Local Python E2E assignment using Playwright (sync), pytest, POM, JSON data, and Allure.
Requirements: [original assignment](docs/assignment/automation-developer-assignment.docx).

## Scope

The suite contains 17 cases:

| Coverage | Cases |
| --- | ---: |
| Search: five shoes under ILS 220, zero under ILS 0.01, 65 across two pages | 3 |
| Invalid search inputs rejected before navigation | 10 |
| Search, add all five items, verify cart count and subtotal (4.2 + 4.3) | 1 |
| Invalid cart URL lists rejected before navigation | 3 |

Section 4.3 extends the existing cart scenario. It compares the displayed **Subtotal**
with `max_price * limit` using `Decimal`, and requires exactly five cart items.
This includes shipping shown by eBay; no checkout-only amounts are estimated.
A failed addition never reduces the expected count or budget.
See [HANDOFF.md](HANDOFF.md) for verified results and remaining work.

## Setup

Prerequisites: Python 3.13, installed Google Chrome, and Node.js/npm for Allure reports.
Run from the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip check
npm ci --no-audit --no-fund
```

If activation is blocked, use `.\.venv\Scripts\python.exe` instead of `python`.
Python dependencies are pinned in `requirements.txt`; `pyproject.toml` configures pytest/Ruff.

## Check and run

```powershell
python -m ruff check .
python -m ruff format --check .
python -m pytest --collect-only --browser-channel chrome -q
```

Run live tests only when cart additions are intended:

```powershell
python -m pytest tests/e2e --run-e2e --browser-channel chrome -vv --log-cli-level=INFO
```

For search only, replace `tests/e2e` with `tests/e2e/test_search_submission.py`.
For the cart scenario and its input checks, use `tests/e2e/test_add_items_to_cart.py`.
Without `--run-e2e`, pytest skips the suite. Tests run locally; there is no CI.

Chrome opens visibly and maximized because pytest's `addopts` includes `--headed`.
Remove that flag to run headlessly. To use bundled Chromium, install it with
`python -m playwright install chromium` and omit `--browser-channel chrome`.

## Reports

```powershell
npm run report
npm run report:open
```

Default results: `artifacts/allure-results`; generated report: `artifacts/allure-report`.
Each run cleans its selected results directory. Use `--alluredir=artifacts/<run-name>`
to preserve earlier evidence, then generate a matching report:

```powershell
npx allure generate artifacts/<run-name> --output artifacts/<run-name>-report
```

If npx is unavailable on PATH, use `node node_modules/allure/cli.js` instead of `npx allure`.

Allure includes stdout, selected variants, random seeds, viewport screenshots, and traces.
Keep `--capture=tee-sys`; do not use `-s`. Open a trace with
`python -m playwright show-trace <trace-attachment.zip>`.

## Configuration and assumptions

- `.env.example` lists settings; real environment variables override `.env`.
- Currency/locale: ILS / en-IL. Other currencies fail parsing explicitly.
- Each test uses a fresh guest browser context; no saved account state or credentials.
  A dedicated identification function remains pending.
- JSON files under `data/` keep search and cart inputs separate. Override them with
  `--case-file`, `--negative-case-file`, `--cart-case-file`, or `--invalid-cart-case-file`.
- Variants are selected from available options with a recorded seed. The final displayed
  subtotal determines the budget outcome, including price changes caused by variants.
- Even when every item's price is under ILS 220, shipping can push Subtotal above ILS 1,100.
  The test must then fail; it does not raise the budget or switch to the Items amount.
- Required unavailable items fail; they are never replaced or silently skipped.
- `EBAY_TRACE=on` retains traces. `off` disables them; `retain-on-failure` covers failures
  known before context cleanup. Do not also enable Playwright's `--tracing`.
- eBay errors and verification challenges can block a run. No CAPTCHA bypass is attempted.
  Runtime evidence and authentication data stay out of Git.

## Structure and submission

[Architecture](docs/architecture.md) describes page objects, flow, helpers, and fixtures.
[ReadMeAIBugs.md](ReadMeAIBugs.md) contains three owner-supplied findings and proposed
corrections, with the AI assistance disclosed.
[AGENTS.md](AGENTS.md) contains project working rules.

Submission repository: [Ni172/ebay-playwright-automation](https://github.com/Ni172/ebay-playwright-automation).
Final submission still requires the remaining assignment work, accessible run evidence,
and verified reviewer access. Publication requires separate approval.
