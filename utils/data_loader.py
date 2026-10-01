import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

REQUIRED_FIELDS = {
    "id",
    "query",
    "max_price",
    "limit",
    "currency",
    "expected_min_results",
    "expected_max_results",
    "expected_page_count",
}
NEGATIVE_REQUIRED_FIELDS = {"id", "query", "max_price", "limit", "expected_message"}


@dataclass(frozen=True)
class SearchCase:
    id: str
    query: str
    max_price: Decimal
    limit: int
    currency: str
    expected_min_results: int
    expected_max_results: int
    expected_page_count: int


@dataclass(frozen=True)
class InvalidSearchCase:
    id: str
    query: str
    max_price: Decimal
    limit: int | Decimal | bool
    expected_message: str


def load_search_cases(path: Path) -> tuple[SearchCase, ...]:
    """Reject invalid cases before any browser interaction starts."""
    rows = json.loads(path.read_text(encoding="utf-8"), parse_float=Decimal)
    if not isinstance(rows, list) or not rows:
        raise ValueError("Test data must be a non-empty JSON array")
    cases = []
    seen_ids = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != REQUIRED_FIELDS:
            raise ValueError(
                "Each case needs id, query, max_price, limit, currency, "
                "expected_min_results, expected_max_results and expected_page_count"
            )
        for field in ("id", "query"):
            if not isinstance(row[field], str) or not row[field].strip():
                raise ValueError(f"{field} must be a non-empty string")
        if row["id"] in seen_ids:
            raise ValueError(f"Duplicate case id: {row['id']}")
        try:
            price = Decimal(str(row["max_price"]))
        except InvalidOperation as exc:
            raise ValueError("max_price must be numeric") from exc
        if not price.is_finite() or price <= 0:
            raise ValueError("max_price must be finite and positive")
        # bool inherits from int, but true/false is not a valid item limit.
        if type(row["limit"]) is not int or row["limit"] <= 0:
            raise ValueError("limit must be a positive integer")
        if row["currency"] != "ILS":
            raise ValueError("Only ILS cases are currently supported")
        for field in ("expected_min_results", "expected_max_results"):
            if type(row[field]) is not int or row[field] < 0:
                raise ValueError(f"{field} must be a non-negative integer")
        if row["expected_min_results"] > row["expected_max_results"]:
            raise ValueError("expected_min_results must not exceed expected_max_results")
        if row["expected_max_results"] > row["limit"]:
            raise ValueError("expected_max_results must not exceed limit")
        if type(row["expected_page_count"]) is not int or row["expected_page_count"] <= 0:
            raise ValueError("expected_page_count must be a positive integer")
        case = SearchCase(
            id=row["id"],
            query=row["query"],
            max_price=price,
            limit=row["limit"],
            currency=row["currency"],
            expected_min_results=row["expected_min_results"],
            expected_max_results=row["expected_max_results"],
            expected_page_count=row["expected_page_count"],
        )
        cases.append(case)
        seen_ids.add(case.id)
    return tuple(cases)


def load_invalid_search_cases(path: Path) -> tuple[InvalidSearchCase, ...]:
    """Load intentionally invalid business inputs without normalizing them as valid cases."""
    rows = json.loads(path.read_text(encoding="utf-8"), parse_float=Decimal)
    if not isinstance(rows, list) or not rows:
        raise ValueError("Negative test data must be a non-empty JSON array")

    cases = []
    seen_ids = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != NEGATIVE_REQUIRED_FIELDS:
            raise ValueError(
                "Each negative case needs id, query, max_price, limit and expected_message"
            )
        if not isinstance(row["id"], str) or not row["id"].strip():
            raise ValueError("Negative case id must be a non-empty string")
        if row["id"] in seen_ids:
            raise ValueError(f"Duplicate negative case id: {row['id']}")
        if not isinstance(row["query"], str):
            raise ValueError("Negative case query must be a string")
        if not isinstance(row["expected_message"], str) or not row["expected_message"].strip():
            raise ValueError("Negative case expected_message must be a non-empty string")
        try:
            max_price = Decimal(str(row["max_price"]))
        except InvalidOperation as exc:
            raise ValueError("Negative case max_price must be Decimal-compatible") from exc
        if not isinstance(row["limit"], (int, Decimal)):
            raise ValueError("Negative case limit must be numeric or boolean")

        case = InvalidSearchCase(
            id=row["id"],
            query=row["query"],
            max_price=max_price,
            limit=row["limit"],
            expected_message=row["expected_message"],
        )
        cases.append(case)
        seen_ids.add(case.id)
    return tuple(cases)
