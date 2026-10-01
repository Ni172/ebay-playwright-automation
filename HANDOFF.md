# Project handoff

Updated: 2026-10-01 (Asia/Jerusalem).

## Current scope

The repository contains a reduced search matrix and one isolated cart scenario in two E2E test files:

- search and cart data use only the `shoes` query, with maximum prices at ILS 0.01 and ILS 220;
- an ILS 220 search with limit five must return five URLs from one page;
- an ILS 0.01 search must return zero URLs from one page without pagination;
- a 65-result ILS 220 search must visit exactly two distinct result pages and record contributions of 60 and 5;
- ten invalid-request cases that must fail before navigation;
- search, random available variant selection, and adding every one of five supplied URLs;
- three invalid add-to-cart URL-list cases that must fail before navigation.

The owner clarified that this assignment must remain E2E-only. Before every code or test change, read the complete assignment and its relevant section. Do not introduce unit, component, mocked, simulated, or deterministic-local tests, and do not expand scenario counts beyond the specifically approved scope.

The project uses Python, Playwright synchronous API, pytest, POM, external JSON data, Decimal money values, reproducible randomness, and Allure. Execution is local through Google Chrome for real eBay scenarios. The repository remote is the public GitHub repository documented in README; credentials, session state, and runtime evidence remain excluded from commits.

## Implemented

- SearchResultsPage submits the external query, uses the visible price filter when available, extracts result URLs with XPath, validates displayed ILS prices, and follows enabled pagination.
- ProductPage uses semantic Playwright locators and short CSS selectors without regular expressions. It chooses random enabled values from native selects and button listboxes and records the selected labels.
- ShoppingFlow validates the supplied eBay URLs, visits every URL in order, selects available variants, confirms each cart addition, records per-item evidence, and returns to search. Required unavailable listings fail with evidence instead of being replaced.
- EbayErrorPage separately recognizes `Something went wrong on our end` and clicks the exact `Go to homepage` link or button. Search recovery is bounded to one retry.
- Every pytest browser context is isolated. Evidence fixtures attach screenshots and traces to Allure.
- Search and cart datasets are separate. Expanding search coverage does not create additional cart mutations.
- All positive and negative search inputs are external JSON data. Negative cases include their expected validation message and use a dedicated loader without converting them into valid business cases.
- The former standalone search-submission test was removed as redundant. Its URL-query and visible-input assertions now run in every external search case.
- SearchResultsPage records the ordered result pages from its latest search so the pagination scenario can assert that more than one page was actually visited.
- SearchResultsPage also records how many unique eligible URLs each visited page contributed, so pagination evidence is measurable rather than inferred only from the final count.

## Verification after the search-test expansion

The reduced E2E suite collects 14 cases: three external search scenarios, ten externally supplied negative request-validation cases in the search module, and one cart scenario. The redundant five-result ILS 2000 case was removed because the pagination scenario already covers that price ceiling. `pip check`, Ruff lint, Ruff formatting, diff validation, and full collection pass after this adjustment.

The owner then ran the search module alone through installed Google Chrome. Thirteen of its fourteen cases passed. `womens-tshirts-under-001-ils` was reported as broken because eBay returned its recognized `Something went wrong on our end` page for the initial `women's t-shirts` submission and again after the single bounded recovery attempt. The failure occurred before applying the ILS 0.01 filter or asserting the result count. Its screenshot, stdout, log, and trace were retained. The later 65-result pagination case passed, and all ten validation cases passed without navigating to eBay, so parameter count is not the demonstrated cause of this failure.

The apostrophe was removed from the failing query. At the owner's explicit request for visible three-page pagination evidence, the pagination target was changed to 121 and its expectation to exactly three distinct result pages. The test prints every visited page URL and the number of eligible unique URLs contributed by that page.

The isolated pagination case was then run through installed Google Chrome and passed in 76.92 seconds. It collected 121 unique eligible URLs across exactly three distinct pages: 60 from page 1, 60 from `_pgn=2`, and 1 from `_pgn=3`. Its result, final-page screenshot, stdout, and Playwright trace are retained separately in `artifacts/allure-pagination-check`, so the preceding search-module evidence was not deleted. The adjusted fewer-than-five query has not yet been rerun.

## Section 4.2 add-to-cart test expansion

The existing cart module was aligned with the assignment signature. It now searches for exactly five URLs and calls `add_items_to_cart(urls)` without an extra expected count or reserve candidates. The test requires the returned added-item URLs to match every supplied URL in the same order and prints each recorded variant selection. Three externally supplied invalid URL-list cases cover an empty list, a blank URL, and a non-eBay URL; all must fail before navigation. The expanded repository collects 17 E2E cases in total. `pip check`, Ruff lint, Ruff formatting, diff validation, and full collection pass.

The isolated 4.2 module was then run through installed Google Chrome with the owner's approval for live cart mutations. All four cases passed in 76.25 seconds. The live case searched for five `shoes` URLs at or below ILS 220, added and confirmed all five in the supplied order, returned through eBay's known error page without repeating any Add to cart action, and attached five per-item screenshots. The three invalid URL-list cases passed without navigation. Four traces were retained in `artifacts/allure-cart-4-2`, and its generated report is in `artifacts/allure-cart-4-2-report`. None of the five live listings required a variant in this run (`variants=none` for every item); the unchanged variant-selection implementation was exercised in the earlier historical run but not by this isolated 4.2 run.

The complete 17-case E2E suite was subsequently run through installed Google Chrome. Fifteen cases passed in 242.97 seconds, including the live five-item cart scenario and every invalid-input case. Two search cases did not pass because eBay returned its recognized `Something went wrong on our end` page. The `t-shirts` pagination case was classified as broken after the initial search and its single bounded recovery both returned the error page. The ILS 0.01 `womens t-shirts` case reached the same error page on results page 6; the flow returned zero URLs and the final visible-search-input assertion then failed because the error page has no search field. This exposes an unverified behavior in pagination error handling: a later-page eBay error can currently be mistaken for the end of available paging. No commit was made from this run. The isolated three-page pagination pass remains the latest successful direct verification of that scenario. The new evidence directory `artifacts/allure-full-e2e-check` contains exactly 17 result files (15 passed, one failed, one broken), 17 traces, and eight screenshots.

Pagination error handling was then corrected so a recognized eBay error after clicking `Next` is not treated as the end of paging. The intended next-page URL is retained, one bounded retry is made after returning through eBay Home, and a second failure raises `EbaySearchError` instead of returning partial results. Requirements installation, `pip check`, Ruff lint, Ruff formatting, diff validation, and collection of all 17 E2E cases passed after the change.

The complete suite was rerun through installed Google Chrome. Sixteen cases passed in 405.92 seconds. The five-item cart case passed, and the 121-result pagination case again passed across exactly three pages with contributions of 60, 60, and 1. The new pagination recovery was exercised twice successfully during the ILS 0.01 case, but eBay later redirected page 10 to `/splashui/challenge`; Playwright reported `net::ERR_ABORTED`, so that case was classified as broken. CAPTCHA/challenge solving or bypass remains explicitly out of scope. No commit was made because the full suite did not pass. `artifacts/allure-full-e2e-retry` contains exactly 17 result files (16 passed and one broken), 17 traces, and eight screenshots.

After observing repeated eBay protection during the expanded matrix, the owner requested that data use only `shoes` and fewer live parameters. The ILS 0.01 `womens t-shirts` case was removed, and the three-page ILS 2000 case was changed from `t-shirts` to `shoes`. Search data now has two positive rows: five `shoes` results at ILS 220 and 121 `shoes` results at ILS 2000. Cart data remains an independent five-item `shoes` case at ILS 220. Negative validation rows also use `shoes` where a nonblank query is needed; they remain because they fail before browser navigation and therefore do not add eBay traffic. The temporary pagination retry and `max_pages` changes were removed at the owner's request. No live run has yet been performed against this reduced matrix.

Manual owner verification of ILS 0.01 showed zero results and no pagination when eBay's visible maximum-price filter was actually applied. Earlier automation URLs lacked `_udhi`, proving that the prior price control had not been submitted. Saved Playwright DOM evidence identifies the exact maximum control as `Maximum Value in ILS` and the button title as `Submit price range`; the previous button locator incorrectly searched for visible `Apply` text that does not exist. Because the assignment function accepts only `maxPrice`, `SearchResultsPage` leaves the optional minimum empty, fills the requested maximum, clicks the exact titled button, waits for navigation, and requires `_udhi` to equal the requested maximum before reading result cards. If the controls are present but submission fails, the flow raises `EbaySearchError` instead of scanning unfiltered pages. Static checks and collection of 16 E2E cases pass. A focused live ILS 220 search was attempted, but eBay returned its recognized error page both initially and after bounded search recovery, before price filtering began; the corrected price interaction therefore remains live-unverified.

The owner then manually verified the corrected business boundaries for `shoes`: `_udhi=0.01` produces zero exact results and no pagination, while `_udhi=220` exposes at least nine pages with 60 items per page. Search data was therefore corrected to two complementary cases without adding tests: ILS 0.01 expects exactly zero URLs and one visited page; ILS 220 requests 121 URLs and expects exactly three visited pages. The separate cart case continues to use the assignment example of ILS 220 with the default five-item limit. The former ILS 2000 search row was removed as unnecessary.

The owner subsequently approved three explicit search rows and restored use of both visible price inputs. Every case fills minimum ILS zero. The regular assignment case uses maximum ILS 220 with limit five; the zero-result case uses maximum ILS 0.01 with limit five; and the pagination case uses maximum ILS 220 with limit 65, requiring exactly two result pages with contributions of 60 and 5. This keeps the assignment's five-item behavior visible while exercising the generalized `limit` parameter across one `Next` transition.

The first isolated Chrome rerun of the regular ILS 220 case was blocked before price filtering because eBay returned its known error page twice. The following isolated ILS 0.01 run reached the price section and exposed a real locator ambiguity: each exact ILS label matched both a text input and a range slider. Both Min and Max locators now explicitly use the `textbox` role with their exact accessible names. The owner approved one Firefox run of the regular ILS 220 case as a browser-specific diagnostic; this does not change the project's primary Chrome target or broaden the scenario set.

Playwright Firefox 155.0 build 1543 was installed for that diagnostic. The selected ILS 220 test could not start in either headed or headless Firefox because Windows returned `BrowserType.launch: spawn UNKNOWN` while launching the Playwright Firefox executable. No browser page was created and no eBay request was made by either attempt. Firefox is therefore locally unavailable for this diagnostic; this is an environment-level launch result, not a test assertion or eBay outcome.

The owner then requested the same isolated ILS 220, limit-five case through bundled Playwright Chromium. Chromium launched and reached the live search results page without the recognized eBay error page. The exact `textbox` role locators resolved successfully, but after the flow attempted to fill minimum ILS zero and maximum ILS 220, eBay's exact `Submit price range` button remained disabled until the ten-second click timeout. The failure screenshot shows the visible Min and Max controls back at their placeholders, so the price filter was not submitted and no result extraction or pagination assertion ran. This run failed in 41.33 seconds; its evidence is retained in `artifacts/allure-chromium-search-220-limit-5`. No code was changed in response to this live UI result.

The owner approved a maximized browser display and an XPath locator for the price submission button. Headed Chromium/Chrome now always receives `--start-maximized`, and every browser context uses the native viewport instead of a forced 1920x1080 resolution. There is no separate display flag to remember; screenshots capture the same visible maximized viewport shown during the interactive run. The exact price-submit locator is XPath `//button[@title='Submit price range']`. Ruff lint, Ruff formatting, and collection of all 17 E2E cases pass after this configuration change. No live eBay case has yet been run with these changes.

The owner reran the isolated Chromium ILS 220, limit-five case. The XPath correctly resolved the price-submit button, but eBay kept it disabled because both values entered through Playwright `fill()` were later cleared by the site's controlled inputs. The retained trace confirms that both fill calls completed, while the failure screenshot shows both fields empty and Max still focused. Price entry now uses user-like sequential keyboard input followed by `Tab` to commit each field; the submit button is still clicked normally and is never force-clicked. Ruff lint, Ruff formatting, and full collection passed, then the same isolated Chromium case passed in 37.84 seconds, applied `_udhi=220`, and collected five eligible URLs. A non-fatal evidence warning reported that viewport content did not finish loading before the screenshot timeout. The new evidence is retained in `artifacts/allure-chromium-search-220-keyboard`.

The two remaining positive search cases were then run separately through Chromium. The ILS 0.01, limit-five case passed in 34.40 seconds, applied the filter, and returned exactly zero eligible URLs; a non-fatal viewport-content warning occurred during evidence capture. Its evidence is retained in `artifacts/allure-chromium-search-001-limit-5`. The separate ILS 220, limit-65 pagination case did not reach price filtering or pagination: eBay returned its recognized search error page for the initial query and again after the single bounded recovery attempt, so the case failed explicitly in 10.38 seconds with `EbaySearchError`. Its evidence is retained in `artifacts/allure-chromium-search-220-limit-65`. No code was changed and no bypass or additional automatic retry was introduced.

At the owner's request, the same ILS 220, limit-65 pagination case was then rerun separately through the installed Google Chrome channel. It passed in 54.01 seconds, collected exactly 65 eligible URLs, and recorded two distinct result pages: 60 URLs from the filtered first-page URL containing `_udhi=220`, followed by five URLs from `_pgn=2`. A non-fatal viewport-content warning occurred during evidence capture. The Chrome evidence is retained in `artifacts/allure-chrome-search-220-limit-65`; no code was changed.

Before the owner-requested commit and push, README and the architecture document were audited against the assignment and current implementation. They now distinguish implemented search/add-to-cart work from pending identification and cart-total stages, describe native maximized browser sizing and the keyboard-driven price inputs, and record the latest isolated live evidence without claiming a combined final run. `python -m pip install -r requirements.txt`, `python -m pip check`, Ruff lint, Ruff formatting, `git diff --check`, and collection of all 17 E2E cases through the installed Chrome channel passed. The live cart scenario was not repeated during this pre-publication verification because it would mutate eBay state and no new mutation approval was given.

## Earlier E2E evidence

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

Allure screenshots use `full_page=False` and capture the visible native browser viewport. Earlier full-page eBay screenshots reached heights above 13,000 pixels, causing Allure to shrink the entire page into an unreadable preview. Headed Chromium/Chrome now starts maximized, so the interactive browser and screenshot evidence use the same customer-sized view while Playwright trace remains available for broader debugging context.

Before each screenshot, the evidence helper conditionally waits up to ten seconds for document completion, loaded fonts, and every image currently intersecting the viewport to finish loading. Screenshot animations are disabled. If an external asset stalls, the helper logs a warning and still captures evidence instead of replacing the test outcome.

## Source

The original assignment is retained unchanged at `docs/assignment/automation-developer-assignment.docx`.
