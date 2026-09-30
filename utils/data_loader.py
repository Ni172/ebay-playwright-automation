import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

REQUIRED_FIELDS = {"id", "query", "max_price", "limit", "currency"}


@dataclass(frozen=True)
class SearchCase:
    id: str
    query: str
    max_price: Decimal
    limit: int
    currency: str


def load_search_cases(path: Path) -> tuple[SearchCase, ...]:
    """Reject invalid cases before any browser interaction starts."""
    rows = json.loads(path.read_text(encoding="utf-8"), parse_float=Decimal)
    if not isinstance(rows, list) or not rows:
        raise ValueError("Test data must be a non-empty JSON array")
    cases = []
    seen_ids = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != REQUIRED_FIELDS:
            raise ValueError("Each case needs id, query, max_price, limit and currency")
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
        case = SearchCase(
            id=row["id"],
            query=row["query"],
            max_price=price,
            limit=row["limit"],
            currency=row["currency"],
        )
        cases.append(case)
        seen_ids.add(case.id)
    return tuple(cases)
