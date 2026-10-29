"""Load, search, and calculate estimates from the local JSON catalog."""

import json
from collections import defaultdict
from pathlib import Path
from statistics import median

from pydantic import ValidationError

from littlecoinapp.models import (
    CatalogCoin,
    CatalogIdentity,
    CoinCatalog,
    CoinIdentity,
    PriceEstimate,
)


class CatalogError(ValueError):
    """The catalog is missing, invalid, or unsupported."""


def load_catalog(path: Path) -> CoinCatalog:
    try:
        contents = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CatalogError(f"Cannot read catalog '{path}': {exc}") from exc

    try:
        return CoinCatalog.model_validate_json(contents)
    except ValidationError as exc:
        raise CatalogError(f"Invalid catalog '{path}': {exc}") from exc


def _normalized(value: str | None) -> str | None:
    if value is None:
        return None
    return " ".join(value.casefold().split())


def _score_match(query: CoinIdentity, candidate: CatalogIdentity) -> int:
    query_country = _normalized(query.country)
    candidate_country = _normalized(candidate.country)
    if query_country and candidate_country and query_country != candidate_country:
        return 0

    query_denomination = _normalized(query.denomination)
    candidate_denomination = _normalized(candidate.denomination)
    if (
        query_denomination
        and candidate_denomination
        and query_denomination != candidate_denomination
    ):
        return 0

    score = 0
    for query_value, candidate_value, weight in (
        (query.country, candidate.country, 3),
        (query.denomination, candidate.denomination, 3),
        (query.coin_type, candidate.coin_type, 2),
        (query.mint_mark, candidate.mint_mark, 1),
        (query.composition, candidate.composition, 1),
    ):
        normalized_query = _normalized(query_value)
        if normalized_query and normalized_query == _normalized(candidate_value):
            score += weight

    if query.year is not None and candidate.year is not None:
        if query.year == candidate.year:
            score += 4
        elif abs(query.year - candidate.year) == 1:
            score += 1

    return score


def retrieve_matches(
    query: CoinIdentity,
    catalog: CoinCatalog,
    limit: int = 5,
) -> list[CatalogCoin]:
    ranked = [
        (_score_match(query, coin.identity), coin)
        for coin in catalog.coins
    ]
    ranked = [(score, coin) for score, coin in ranked if score > 0]
    ranked.sort(key=lambda result: (-result[0], result[1].id.casefold()))
    return [coin for _, coin in ranked[:limit]]


def estimate_prices(matches: list[CatalogCoin]) -> list[PriceEstimate]:
    sales_by_currency: dict[str, list[float]] = defaultdict(list)
    for coin in matches:
        for observation in coin.valuations:
            if observation.kind == "realized_sale":
                sales_by_currency[observation.currency].append(observation.amount)

    return [
        PriceEstimate(
            currency=currency,
            low=min(amounts),
            median=median(amounts),
            high=max(amounts),
            sale_count=len(amounts),
        )
        for currency, amounts in sorted(sales_by_currency.items())
    ]
