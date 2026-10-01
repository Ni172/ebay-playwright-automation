# Project handoff

Updated: 2026-10-01 (Asia/Jerusalem).

## Approved scope

The owner approved section 4.3, an audit of existing code/fixtures/tests/docs, and visible
local E2E execution, followed by an explicit request to commit and push these changes.
No new scenarios, test layers, or CI were requested.
Read the complete [assignment](docs/assignment/automation-developer-assignment.docx) before
further code changes. Follow [AGENTS.md](AGENTS.md); ask before advancing to another stage.

## Current implementation

- Python, synchronous Playwright, pytest, POM, external JSON, Decimal, and Allure.
- Three `shoes` search cases: five results under ILS 220, zero under ILS 0.01,
  and 65 under ILS 220 across two pages (60 + 5).
- Ten invalid search requests and three invalid cart URL lists fail before navigation.
- One shopping scenario searches for exactly five URLs, adds every URL in order,
  records available-variant selections, and verifies cart count and budget.
- Section 4.3 uses `CartPage` and `assert_cart_total_not_exceeds`. It reads the site's
  **Subtotal**, including displayed shipping, and compares it with ILS 220 x 5.
  Missing additions never reduce the expected count or budget.
- Each test has a fresh guest context; no account state is loaded or cleared.
- Browser lifecycle and cleanup belong to pytest-playwright. Project fixtures own traces.
  Chrome is headed/maximized with a native viewport; screenshots capture that viewport.

## Audit changes

- Added 4.3 to the existing shopping scenario without duplicating it; the suite remains 17 cases.
- Removed the unused `search_cases` fixture. Existing page/context isolation remains intact.
- Check page counts in every search case, including zero results. Exact per-page contributions
  are now external JSON expectations, validated by the data loader.
- Known eBay errors after price filtering or pagination now raise `EbaySearchError` instead
  of being mistaken for zero results or the end of paging. No extra retry was introduced.
- Shortened README and architecture documentation and corrected the diagram to match real calls.

## Verification on 2026-10-01

`pip install -r requirements.txt`, `pip check`, Ruff lint/format, and collection of all
17 cases passed. Generated evidence stays under ignored `artifacts/`.

| Run | Result | Evidence directory |
| --- | --- | --- |
| Initial full Chrome run | 15 passed, 2 failed in 230.14 s | `artifacts/allure-stage-4-3` |
| Search after error-handling/data fixes | 2 passed, 1 broken in 143.61 s | `artifacts/allure-stage-4-3-search-check` |
| Corrected Subtotal run | 3 passed, 1 failed in 130.34 s | `artifacts/allure-stage-4-3-subtotal` |

The initial run used the Items amount (ILS 756.38) and passed its provisional cart assertion.
Visual inspection showed eBay labels ILS 1,543.89 as Subtotal, including ILS 787.51 shipping.
The owner instructed strict adherence to the document, so the implementation was corrected
to read `[data-test-id="SUBTOTAL"]`. The earlier Items-based pass is **not** final 4.3 evidence.

The corrected run confirmed all five additions and the exact cart count. It read Items
ILS 667.25 plus shipping ILS 694.22 as Subtotal ILS 1,361.47, then correctly failed the
ILS 1,100 budget assertion. All three invalid-cart cases passed. Four traces and seven
screenshots were retained, and `artifacts/allure-stage-4-3-subtotal-report/index.html`
was generated and its 3-pass/1-failure summary verified. None of these five listings
required variants, so this run does not revalidate the variant-selection branches.

The initial full run's two search failures were eBay error pages after filtering.
The corrected search run passed five-result and zero-result cases; pagination reached
page two and raised the new explicit error on eBay's error screen. The initial run had
successfully collected 65 URLs as 60 + 5. Do not present these as a combined all-green run.

The initial run retained 17 traces and nine screenshots; the search check retained three
traces and three screenshots. Separate Allure reports were generated in each matching
`-report` directory. Non-fatal screenshot-readiness warnings did not suppress evidence.

## Section 5: owner-supplied bug review

The owner approved documenting three findings: fixture-managed resource lifecycle,
condition-based waits instead of sleeps, and POM separation. Browser setup and closing
are one finding. Sync API usage and the absence of a Page type import are not labeled bugs.
`ReadMeAIBugs.md` includes original excerpts, explanations, and one illustrative correction.
The example URL/selectors are unverified and the snippet was not executed. Only Markdown
files changed; no tests or live-site actions were performed for this stage. The owner
subsequently approved committing and pushing these documentation changes.

## Remaining work and limits

- Complete a recognizable identification function as Guest behavior or Login Stub in an approved stage.
- `ReadMeAIBugs.md` contains the owner's three agreed findings, explanations, and corrections.
- Live listings, availability, variants, delivery costs, and eBay errors remain external.
  Subtotal can exceed the budget even when every item passes the search price filter.
- CAPTCHA solving/bypass is out of scope. A preliminary direct cart inspection encountered
  a challenge; no bypass was attempted. Later ordinary shopping navigation reached the cart.
- The owner approved publishing the current 4.3 changes; final submission and reviewer
  access verification remain pending.

## Commands

The owner requested restoring complete newcomer setup instructions. README now includes
Windows prerequisite installation (including Node.js/npm), cloning, virtual-environment
setup, full/module/single-scenario commands, and Allure generation/opening and troubleshooting.
Keep these operational instructions when shortening documentation.

Verification: installed requirements successfully in a new Python 3.13.9 environment under
`artifacts/readme-install-check`; pip check and all 17 collected cases passed there. The
single pagination command selected one case. `npm ci` installed 156 packages from the lockfile.
Allure generated `artifacts/readme-allure-check` from existing cart evidence and served it
successfully on localhost:8766 (HTTP 200). Its summary retained three passes and one failure.
Ruff passed in the project environment; all four documented winget package IDs resolved.
No live eBay tests were rerun during this documentation update.

Use the virtual environment and the commands in [README.md](README.md). Keep `EBAY_TRACE=on`
for evidence and do not also enable plugin tracing. Use a separate `--alluredir` for each run.
The installed Allure CLI can be invoked directly if npm/npx is absent from the current PATH:

```powershell
node node_modules/allure/cli.js generate artifacts/<run> --output artifacts/<run>-report
```

Earlier historical evidence remains in `artifacts/`; prior implementation history remains in Git.
