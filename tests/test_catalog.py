import json
import tempfile
import unittest
from pathlib import Path

from littlecoinapp.catalog import (
    CatalogError,
    estimate_prices,
    load_catalog,
    retrieve_matches,
)
from littlecoinapp.models import CoinCatalog, CoinIdentity


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.catalog = CoinCatalog.model_validate(
            {
                "schema_version": 1,
                "coins": [
                    {
                        "id": "penny-1914",
                        "identity": {
                            "country": "United States",
                            "denomination": "1 cent",
                            "year": 1914,
                            "mint_mark": "D",
                            "coin_type": "Lincoln cent",
                            "composition": "bronze",
                        },
                        "valuations": [
                            {
                                "kind": "realized_sale",
                                "amount": 12,
                                "currency": "USD",
                                "date": "2025-01-02",
                                "source": "Auction result",
                            },
                            {
                                "kind": "asking_price",
                                "amount": 999,
                                "currency": "USD",
                                "source": "Dealer listing",
                            },
                        ],
                    },
                    {
                        "id": "euro-cent",
                        "identity": {
                            "country": "France",
                            "denomination": "1 cent",
                            "year": 2002,
                        },
                        "valuations": [],
                    },
                ],
            }
        )
        self.query = CoinIdentity(
            country="United States",
            denomination="1 cent",
            year=1914,
            mint_mark="D",
            coin_type="Lincoln cent",
            description="Coin in photo",
            confidence=0.9,
        )

    def test_retrieval_ranks_matching_coin_and_excludes_other_country(self):
        matches = retrieve_matches(self.query, self.catalog)

        self.assertEqual([coin.id for coin in matches], ["penny-1914"])

    def test_estimate_uses_realized_sales_only(self):
        estimates = estimate_prices(retrieve_matches(self.query, self.catalog))

        self.assertEqual(len(estimates), 1)
        self.assertEqual(estimates[0].currency, "USD")
        self.assertEqual(estimates[0].low, 12)
        self.assertEqual(estimates[0].median, 12)
        self.assertEqual(estimates[0].high, 12)
        self.assertEqual(estimates[0].sale_count, 1)

    def test_empty_catalog_has_no_estimate(self):
        self.assertEqual(estimate_prices([]), [])

    def test_load_catalog_reports_invalid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            path.write_text("{invalid", encoding="utf-8")

            with self.assertRaises(CatalogError):
                load_catalog(path)

    def test_initial_catalog_is_valid_and_empty(self):
        project_catalog = Path(__file__).parents[1] / "data" / "catalog.json"

        self.assertEqual(load_catalog(project_catalog).coins, [])


if __name__ == "__main__":
    unittest.main()
