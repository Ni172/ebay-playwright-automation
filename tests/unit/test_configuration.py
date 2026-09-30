import json
from decimal import Decimal

import pytest

from config.settings import Settings
from utils.data_loader import load_search_cases

pytestmark = pytest.mark.unit


def test_environment_overrides_defaults(monkeypatch):
    monkeypatch.setenv("EBAY_TIMEOUT_MS", "1500")
    assert Settings.from_env().timeout_ms == 1500


@pytest.mark.parametrize(
    "overrides",
    [
        {"timeout_ms": 0},
        {"currency": "EUR"},
        {"locale": "en-US"},
        {"trace": "invalid"},
        {"base_url": "file:///private"},
    ],
)
def test_invalid_settings_fail_early(overrides):
    with pytest.raises(ValueError):
        Settings(**overrides)


def test_external_case_is_typed(search_case):
    assert isinstance(search_case.max_price, Decimal)
    assert search_case.max_price.is_finite()
    assert search_case.limit > 0


@pytest.mark.parametrize(
    "field,value",
    [
        ("max_price", "NaN"),
        ("limit", True),
        ("query", " "),
        ("currency", "EUR"),
    ],
)
def test_invalid_case_fails_before_browser_launch(tmp_path, field, value):
    row = {"id": "case", "query": "shoes", "max_price": "10", "limit": 5, "currency": "ILS"}
    row[field] = value
    path = tmp_path / "cases.json"
    path.write_text(json.dumps([row]), encoding="utf-8")
    with pytest.raises(ValueError):
        load_search_cases(path)
