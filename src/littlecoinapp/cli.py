"""Command-line entry point for littlecoinapp."""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAIError

from littlecoinapp.catalog import CatalogError, estimate_prices, load_catalog, retrieve_matches
from littlecoinapp.models import CatalogCoin, CoinIdentity, PriceEstimate
from littlecoinapp.vision import identify_coin


def _format_identity(identity: CoinIdentity) -> list[str]:
    fields = (
        ("Country", identity.country),
        ("Denomination", identity.denomination),
        ("Year", identity.year),
        ("Mint mark", identity.mint_mark),
        ("Coin type", identity.coin_type),
        ("Composition", identity.composition),
        ("Visible condition", identity.condition),
    )
    lines = [f"  {label}: {value}" for label, value in fields if value is not None]
    lines.extend(
        [
            f"  Confidence: {identity.confidence:.0%}",
            f"  Notes: {identity.description}",
        ]
    )
    return lines


def _format_report(
    identity: CoinIdentity,
    matches: list[CatalogCoin],
    estimates: list[PriceEstimate],
) -> str:
    lines = ["Coin identification:", *_format_identity(identity), "", "Catalog matches:"]
    if not matches:
        lines.append("  No matching catalog entries found.")
    for coin in matches:
        details = ", ".join(
            str(value)
            for value in (
                coin.identity.country,
                coin.identity.denomination,
                coin.identity.year,
                coin.identity.coin_type,
            )
            if value is not None
        )
        lines.append(f"  {coin.id}: {details or 'coin details not provided'}")
        for valuation in coin.valuations:
            date = f", {valuation.date.isoformat()}" if valuation.date else ""
            lines.append(
                f"    {valuation.kind}: {valuation.amount:.2f} "
                f"{valuation.currency} ({valuation.source}{date})"
            )

    lines.extend(["", "Preliminary value from recorded realized sales:"])
    if not estimates:
        lines.append("  Not available: no realized-sale prices in the matches.")
    for estimate in estimates:
        lines.append(
            f"  {estimate.low:.2f}–{estimate.high:.2f} {estimate.currency} "
            f"(median {estimate.median:.2f}; {estimate.sale_count} sale(s))"
        )
    lines.append("This is a research aid, not a professional appraisal.")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="littlecoin",
        description="Identify a coin photo and look up local catalog valuations.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    analyze = commands.add_parser("analyze", help="Identify and value a coin photo")
    analyze.add_argument("image", type=Path, help="Path to a coin photo")
    analyze.add_argument(
        "--catalog",
        type=Path,
        default=Path("data/catalog.json"),
        help="Path to the local JSON catalog (default: data/catalog.json)",
    )
    analyze.add_argument(
        "--matches",
        type=int,
        default=5,
        help="Maximum number of catalog entries to retrieve (default: 5)",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.matches < 1:
        parser.error("--matches must be at least 1")

    try:
        catalog = load_catalog(args.catalog)
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set. Add it to the project .env file "
                "or the environment."
            )
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        identity = identify_coin(args.image, model)
        matches = retrieve_matches(identity, catalog, args.matches)
        estimates = estimate_prices(matches)
        print(_format_report(identity, matches, estimates))
        return 0
    except (CatalogError, OpenAIError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
