"""Utilities for fetching FX rates.

Design goals:
- Practical + efficient: one HTTP call, cached at the UI layer.
- No secrets required by default (works out of the box).
- Clean-code: small, testable functions; clear fallbacks.

We compute a mapping in the form:
  kurs_idr[CCY] = IDR per 1 unit CCY
Example:
  kurs_idr['USD'] = 15750.0  # 1 USD = 15750 IDR
  kurs_idr['EUR'] = 17000.0  # 1 EUR = 17000 IDR
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable
import json
import urllib.request


DEFAULT_CURRENCIES: list[str] = [
    "IDR",
    "USD",
    "EUR",
    "JPY",
    "GBP",
    "AUD",
    "CNY",
    "SGD",
    "MYR",
    "THB",
]

# Fallback for offline/demo: kept close to current app behavior.
KURS_IDR_FALLBACK: dict[str, float] = {
    "IDR": 1.0,
    "USD": 15750.0,
    "EUR": 17000.0,
    "JPY": 105.0,
    "GBP": 20000.0,
    "AUD": 10200.0,
    "CNY": 2200.0,
    "SGD": 11700.0,
    "MYR": 3550.0,
    "THB": 450.0,
}


@dataclass(frozen=True)
class RatesSnapshot:
    kurs_idr: dict[str, float]
    source: str
    as_of: str | None
    fetched_at_utc: datetime
    warnings: tuple[str, ...] = ()


def _fetch_json(url: str, *, timeout_s: int = 10) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "pds-streamlit/1.0 (+https://github.com/fsyakz/pds)",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:  # nosec - fixed URL
        raw = resp.read()
    payload = json.loads(raw.decode("utf-8"))
    return payload if isinstance(payload, dict) else {}


def fetch_usd_base_rates(*, timeout_s: int = 10) -> tuple[dict[str, float], str | None]:
    """Fetch FX rates with base USD.

    Uses a no-key public endpoint. We only need the `rates` map.
    Returns: (rates, as_of)
    """

    # Public endpoint (no API key) that returns:
    # { result: 'success', time_last_update_utc, rates: { 'IDR': 15xxx, ... } }
    url = "https://open.er-api.com/v6/latest/USD"
    payload = _fetch_json(url, timeout_s=timeout_s)

    if payload.get("result") != "success":
        return {}, None

    rates = payload.get("rates")
    if not isinstance(rates, dict):
        return {}, None

    out: dict[str, float] = {}
    for k, v in rates.items():
        if isinstance(k, str) and isinstance(v, (int, float)):
            out[k.upper()] = float(v)

    as_of = payload.get("time_last_update_utc")
    return out, (str(as_of) if as_of is not None else None)


def compute_kurs_idr_from_usd_base(
    rates_usd_base: dict[str, float],
    *,
    currencies: Iterable[str] | None = None,
) -> dict[str, float]:
    """Convert a USD-base rates map into IDR-per-currency mapping.

    Assumes rates are of the form: 1 USD = rates[currency] currency.
    Then: 1 CCY = (IDR per USD) / (CCY per USD)
    """

    if "IDR" not in rates_usd_base or "USD" not in rates_usd_base:
        return {}

    idr_per_usd = float(rates_usd_base["IDR"])

    wanted = [c.upper() for c in (currencies or DEFAULT_CURRENCIES)]
    # Keep order stable + unique.
    seen: set[str] = set()
    ordered: list[str] = []
    for c in wanted:
        if c and c not in seen:
            seen.add(c)
            ordered.append(c)

    kurs_idr: dict[str, float] = {}
    for ccy in ordered:
        if ccy == "IDR":
            kurs_idr["IDR"] = 1.0
            continue
        if ccy == "USD":
            kurs_idr["USD"] = idr_per_usd
            continue

        per_usd = rates_usd_base.get(ccy)
        if isinstance(per_usd, (int, float)) and float(per_usd) > 0:
            kurs_idr[ccy] = idr_per_usd / float(per_usd)

    # Ensure base is present.
    kurs_idr.setdefault("IDR", 1.0)
    if "USD" in rates_usd_base:
        kurs_idr.setdefault("USD", idr_per_usd)

    return kurs_idr


def get_rates_snapshot(
    *,
    currencies: Iterable[str] | None = None,
    timeout_s: int = 10,
) -> RatesSnapshot:
    """Get a rates snapshot with safe fallbacks."""

    fetched_at = datetime.now(timezone.utc)

    warnings: list[str] = []
    try:
        rates_usd, as_of = fetch_usd_base_rates(timeout_s=timeout_s)
        kurs_idr = compute_kurs_idr_from_usd_base(rates_usd, currencies=currencies)
        if kurs_idr:
            return RatesSnapshot(
                kurs_idr=kurs_idr,
                source="realtime:open.er-api.com (base USD)",
                as_of=as_of,
                fetched_at_utc=fetched_at,
                warnings=tuple(warnings),
            )
        warnings.append("Respon API tidak berisi kurs yang dibutuhkan (IDR/USD).")
    except Exception as e:
        warnings.append(f"Gagal mengambil kurs realtime: {type(e).__name__}: {e}")

    return RatesSnapshot(
        kurs_idr=dict(KURS_IDR_FALLBACK),
        source="fallback:static (demo)",
        as_of=None,
        fetched_at_utc=fetched_at,
        warnings=tuple(warnings),
    )
