"""Validated configuration; loading .env is an explicit pytest bootstrap step."""

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    base_url: str = "https://www.ebay.com"
    locale: str = "en-US"
    currency: str = "USD"
    timeout_ms: int = 10_000
    navigation_timeout_ms: int = 30_000
    random_seed: int = 20260930
    trace: str = "on"

    def __post_init__(self) -> None:
        url = urlsplit(self.base_url)
        if url.scheme not in {"http", "https"} or not url.hostname or url.username:
            raise ValueError("EBAY_BASE_URL must be an HTTP(S) URL without credentials")
        if self.currency != "USD" or self.locale != "en-US":
            raise ValueError("Only USD / en-US parsing is currently supported")
        if self.timeout_ms <= 0 or self.navigation_timeout_ms <= 0:
            raise ValueError("Timeouts must be positive milliseconds")
        if self.trace not in {"on", "off", "retain-on-failure"}:
            raise ValueError("EBAY_TRACE must be on, off, or retain-on-failure")

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            base_url=os.getenv("EBAY_BASE_URL", "https://www.ebay.com"),
            locale=os.getenv("EBAY_LOCALE", "en-US"),
            currency=os.getenv("EBAY_CURRENCY", "USD"),
            timeout_ms=int(os.getenv("EBAY_TIMEOUT_MS", "10000")),
            navigation_timeout_ms=int(os.getenv("EBAY_NAVIGATION_TIMEOUT_MS", "30000")),
            random_seed=int(os.getenv("EBAY_RANDOM_SEED", "20260930")),
            trace=os.getenv("EBAY_TRACE", "on"),
        )
