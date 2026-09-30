"""Live search submission check; product extraction is a later stage."""

from urllib.parse import parse_qs, urlsplit

import allure
import pytest
from playwright.sync_api import expect

from pages.search_results_page import SearchResultsPage

pytestmark = pytest.mark.e2e


def test_search_submits_external_case(page, search_case, screenshot):
    search_page = SearchResultsPage(page)

    with allure.step("Open the eBay search homepage"):
        response = search_page.open_search_home()
        allure.dynamic.parameter("homepage_status", response.status)

    with allure.step("Submit the external search query"):
        search_page.search(search_case.query)

    with allure.step("Confirm the results URL carries the submitted query"):
        query_parameters = parse_qs(urlsplit(page.url).query)
        assert query_parameters.get("_nkw") == [search_case.query]
        expect(search_page.search_input).to_have_value(search_case.query)
        screenshot("search-results")
