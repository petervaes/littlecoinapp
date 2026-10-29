"""Data models shared by vision analysis and the local coin catalog."""

from datetime import date as Date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CoinIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    country: str | None = Field(default=None, description="Issuing country")
    denomination: str | None = Field(default=None, description="Face value")
    year: int | None = Field(default=None, description="Year minted")
    mint_mark: str | None = Field(default=None, description="Mint mark, if visible")
    coin_type: str | None = Field(default=None, description="Coin name or type")
    composition: str | None = Field(default=None, description="Metal or composition")
    condition: str | None = Field(
        default=None,
        description="Visible condition; do not claim a certified grade",
    )
    description: str = Field(
        description="Visible design details and any identification uncertainty"
    )
    confidence: float = Field(ge=0, le=1, description="Identification confidence")


class CatalogIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    country: str | None = None
    denomination: str | None = None
    year: int | None = None
    mint_mark: str | None = None
    coin_type: str | None = None
    composition: str | None = None
    condition: str | None = None


class ValuationObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal[
        "realized_sale",
        "asking_price",
        "expert_appraisal",
        "ai_estimate",
    ]
    amount: float = Field(gt=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    date: Date | None = None
    source: str
    grade: str | None = None
    notes: str | None = None


class CatalogCoin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    identity: CatalogIdentity
    notes: str | None = None
    valuations: list[ValuationObservation] = Field(default_factory=list)


class CoinCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1]
    coins: list[CatalogCoin] = Field(default_factory=list)


class PriceEstimate(BaseModel):
    currency: str
    low: float
    median: float
    high: float
    sale_count: int
