# littlecoinapp

A Python CLI that identifies a coin from a photo with OpenAI vision, retrieves
similar entries from a local JSON catalog, and calculates a preliminary value
range from recorded realized-sale prices.

The catalog is the source of valuation data: the app does not invent market
prices or use an external price database. If it cannot find comparable sales,
it reports that it cannot estimate a value.

## Requirements

- Python 3.11 or newer
- An OpenAI API key with access to a vision-capable model

## Local setup (Windows PowerShell)

The project virtual environment is `.venv` in the project directory.

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
Copy-Item .env.example .env
```

Set `OPENAI_API_KEY` in `.env`. The default model is `gpt-4o-mini`; change
`OPENAI_MODEL` if you want to use another compatible vision model.

## Identify and value a coin

Run commands from the project directory:

```powershell
littlecoin analyze .\path\to\coin-photo.jpg
```

Supported photo formats are JPEG, PNG, WebP, and GIF. You can select a
different catalog or limit the number of retrieved entries:

```powershell
littlecoin analyze .\coin.png --catalog .\data\catalog.json --matches 5
```

The analysis identifies visible coin attributes. The app then ranks matching
catalog entries locally and reports the median and range of their recorded
realized-sale prices, grouped by currency. Asking prices and AI estimates are
shown as catalog information but are not used to calculate the range. If no
matching realized sales are available, no value is reported.

## Local catalog

Edit [`data/catalog.json`](data/catalog.json) to add coin references and
valuation observations. Keep one entry per reference coin. Each entry has:

- `id`: a unique identifier for the reference entry
- `identity`: known coin attributes (`country`, `denomination`, `year`,
  `mint_mark`, `coin_type`, and `composition`; `condition` and `description`
  are optional)
- `notes`: optional identifying details
- `valuations`: observations with `kind`, `amount`, `currency`, `date`,
  `source`, and optional `grade` or `notes`

Valuation `kind` must be one of `realized_sale`, `asking_price`,
`expert_appraisal`, or `ai_estimate`. Record a realized sale only when you have
a trustworthy sale result; include its source and date where possible.
Currencies are three-letter ISO codes such as `USD` or `EUR`. A catalog entry
can start with only the required fields below; optional identity fields can be
added as they become known:

```json
{
  "schema_version": 1,
  "coins": [
    {
      "id": "your-unique-reference-id",
      "identity": {
        "country": "United States",
        "denomination": "1 cent",
        "year": 1943,
        "coin_type": "Lincoln cent"
      },
      "notes": "Optional reference details",
      "valuations": [
        {
          "kind": "realized_sale",
          "amount": 1.25,
          "currency": "USD",
          "date": "2025-01-15",
          "source": "Name or URL of the sale record",
          "grade": "Optional grade",
          "notes": "Optional sale details"
        }
      ]
    }
  ]
}
```

The initial catalog is empty. Accuracy depends on the quality, quantity, and
condition comparability of entries you add. Retrieval is local and
field-based—there is no vector database or external catalog download. The
reported range is a simple summary of matching sale observations; it does not
adjust for condition or certify authenticity. Treat it as a research aid, not
as a professional appraisal or a guaranteed sale price.

## Development

```powershell
python -m unittest discover -s tests
```

## Project layout

```text
data/catalog.json                 Local coin references and valuations
src/littlecoinapp/                CLI, vision client, catalog retrieval
tests/                            Offline unit tests
.env.example                      Environment variable template
```
