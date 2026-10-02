# Project handoff

Updated: 2026-10-02 (Asia/Jerusalem).

## PR 1 review and locator cleanup (2026-10-02)

Completed: reviewed PR #1 and the full repository against the assignment, with emphasis on the
README and smart locators. `ProductPage` now uses the observed product-region and `data-testid`
CSS selectors for variants, Add to cart, and the confirmation layer. The obsolete `#gh-cart-n`
lookup and page-wide option collection were removed; custom options are scoped to the visible
listbox. `CartPage` and `EbayErrorPage` now follow the same named-selector and locator-property
structure as `SearchResultsPage`.

Added the assignment's explicit Guest identification through `identify_as_guest()`. README now
summarizes all four required responsibilities, distinguishes non-live checks from live results,
explains mutation behavior, documents the locator strategy, and reports the latest verified
outcome without claiming an all-green suite. Architecture documentation was aligned. `.gitignore`
was reviewed and required no change.

Verified: `pip check`, Ruff lint, Ruff format, and collection of all 17 E2E cases passed. The saved
Playwright trace confirms the selected product, cart, and error-page CSS attributes against the
previous live DOM.

Follow-up live evidence showed that Add to cart succeeded, but the confirmation title was outside
the former `x-atc-layer-v3` content element. The confirmation locator now targets the visible
`ux-overlay` dialog containing that content, using stable test and ARIA attributes. The subsequent
live cart scenario confirmed all five additions and reached the final budget assertion. It correctly
failed because the ILS 1,434.56 Subtotal exceeded the ILS 1,100.00 budget. None of the five listings
required variants, so native-select and custom-listbox variant branches remain live-unverified.

## Agent coding-guidance update (2026-10-02)

Completed: refined `AGENTS.md` with concise defensive-coding rules for module-level imports,
narrow exception handling, accurate errors, missing-value validation, dead-code removal, safe
pytest control flow, and meaningful constants. Comments should remain beside the relevant logic
inside functions or methods and normally use no more than one or two precise lines.

No product code, tests, scenarios, or live eBay behavior changed. No test execution was needed for
this documentation-only update.

## Home-recovery hardening and positive execution (2026-10-02)

Completed: added two full-search attempts through `SearchResultsPage._SEARCH_ATTEMPTS`. When the
known eBay error page appears during search submission, price filtering, or pagination, the test
clicks **Go to homepage** and restarts the complete search/filter/collection sequence once.
Exhausting the attempts fails with evidence and never treats an error as zero results.

Verified: Ruff lint/format and collection of all 17 E2E cases passed after this change. A live run
of the four positive scenarios immediately before the change produced 3 passes and 1 expected
budget failure: the cart had all five requested items, but its ILS 1,711.50 Subtotal exceeded the
ILS 1,100.00 threshold. The corresponding report is in
`artifacts/allure-positive-20261002-report`.

The earlier live check established that eBay can return the known error page during pagination. The
full-search loop above has not yet been run against that condition. No mocked or simulated test was
added, per project policy.

## Results-page URL wait (2026-10-02)

Completed: results-page transitions after a price filter or pagination wait up to 30 seconds for
the URL to change, replacing the former five-second limit. The page then waits for
`domcontentloaded`; eBay's ongoing background requests make `networkidle` unsuitable here.

## Documentation and E2E default update (2026-10-02)

Completed: removed the `--run-e2e` pytest option and its collection-time skip behavior.
The repository now runs its real eBay E2E tests by default. README, pytest marker metadata,
and this handoff no longer refer to that option. Removed `npx.cmd` commands, Node/npm fallback
instructions, and the related troubleshooting entry; Allure documentation retains only
`npm run report` and `npm run report:open`.

Verified: `pytest --collect-only --browser-channel chrome -q` collected all 17 cases without
the removed option. No live eBay run or Allure report generation was performed for this change.

## Troubleshooting clarification (2026-10-02)

Completed: README now puts eBay error pages, CAPTCHA, and unavailable listings first in
Troubleshooting. It documents the actual one-time recovery through eBay's **Go to homepage**
control; a repeated error fails with preserved evidence. It also explains that a confirmed cart
addition is never repeated when return-to-search fails.

The guest-context and local-only constraints are described in plain language. The owner removed
the empty-Allure-report note because it is not a project problem. No test code or live execution
was changed for this documentation-only update.

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

The owner requested restoring complete newcomer setup instructions. README includes Windows
prerequisite installation, cloning, virtual-environment setup, full/module/single-scenario
commands, and the standard Allure report generation/opening commands.

Verification: installed requirements successfully in a new Python 3.13.9 environment under
`artifacts/readme-install-check`; pip check and all 17 collected cases passed there. The
single pagination command selected one case. `npm ci` installed 156 packages from the lockfile.
Allure generated `artifacts/readme-allure-check` from existing cart evidence and served it
successfully on localhost:8766 (HTTP 200). Its summary retained three passes and one failure.
Ruff passed in the project environment; all four documented winget package IDs resolved.
No live eBay tests were rerun during this documentation update.

Use the virtual environment and the commands in [README.md](README.md). Keep `EBAY_TRACE=on`
for evidence and do not also enable plugin tracing. Use a separate `--alluredir` for each run.

Earlier historical evidence remains in `artifacts/`; prior implementation history remains in Git.
