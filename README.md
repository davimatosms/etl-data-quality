# ETL Data Quality

Educational ETL pipeline for validating, transforming, and loading Brazilian
public data into PostgreSQL.

> Educational MVP built with production-oriented practices. No real users,
> intentionally small enough to run locally.

[![CI](https://github.com/davimatosms/etl-data-quality/actions/workflows/ci.yml/badge.svg)](https://github.com/davimatosms/etl-data-quality/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Python · Pandas · PostgreSQL · Docker · GitHub Actions

> **Part of a two-repo system.** This project works together with
> [Data Quality API](https://github.com/davimatosms/data-quality-api):
> the ETL runs the validations, the API tracks the health of each run.

## Table of contents

- [The problem](#the-problem)
- [Architecture](#architecture)
- [Quick start](#quick-start)
- [Quick start with PostgreSQL](#quick-start-with-postgresql)
- [Usage](#usage)
- [Technical decisions](#technical-decisions)
- [Testing and quality](#testing-and-quality)
- [Project structure](#project-structure)
- [Known limitations and next steps](#known-limitations-and-next-steps)
- [Related projects](#related-projects)
- [License](#license)

## The problem

Public datasets commonly contain malformed identifiers, inconsistent
encodings, missing fields, invalid dates, duplicated records, and inconsistent
types. Loading these values without validation can silently corrupt downstream
analysis.

This pipeline keeps the raw input, validates each row, records rejected rows
with their reasons, transforms accepted rows, and loads only accepted data
into PostgreSQL. It is a quality-checking machine for Brazilian company data:
it reads a CSV, separates accepted and rejected rows, normalizes accepted
values such as CNPJ, and keeps rejected rows auditable in quarantine.

## Architecture

The two repositories work together as follows:

```text
┌──────────────────────────┐
│ ETL Data Quality         │
│ extract → validate →     │
│ transform → load         │
└────────────┬─────────────┘
             │ POST /sources/{id}/checks
             ▼
┌──────────────────────────┐
│ Data Quality API         │
│ FastAPI + Pydantic       │
│ freshness on read        │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ PostgreSQL               │
│ sources + checks + rules │
└──────────────────────────┘
```

Inside this repository, the default CLI pipeline is:

```text
CSV/API input
    |
    v
Extract  -> timestamped copy in data/raw/
    |
    v
Validate -> valid rows + rejected rows
    |                         |
    |                         v
    |                   local quarantine CSV
    |                         |
    |                         v
    |                   PostgreSQL quarantine
    v
Transform -> canonical CNPJ, dates, and text
    |
    v
Load -> PostgreSQL upsert into empresas
    |
    v
Report -> JSON metrics + structured logs
```

The ETL remains responsible for validation. After a run, it can report the
execution timestamp, `PASSING`/`FAILING` status, rule results, and metrics to
the companion API. The API integration is optional; without its environment
variables, the pipeline behaves as a local ETL.

## Quick start

The following demo runs without a database and takes less than two minutes.
It uses the intentionally problematic sample at
`tests/fixtures/sample_dirty_data.csv`.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

python -m src.pipeline \
  --input tests/fixtures/sample_dirty_data.csv
```

<details>
<summary>Windows (PowerShell)</summary>

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

python -m src.pipeline `
  --input tests/fixtures/sample_dirty_data.csv
```

</details>

The sample contains three rows: one valid company, one row without a CNPJ,
and one duplicate CNPJ. The report should show three rows read, one accepted,
and two rejected. Accepted CNPJs are shown in canonical form, without
punctuation, and rejected rows are written under `data/quarantine/`.

Inspect the generated quarantine file with:

```bash
find data/quarantine -type f -maxdepth 1 -print -exec cat {} \;
```

<details>
<summary>Windows (PowerShell)</summary>

```powershell
Get-ChildItem data\quarantine
Get-Content data\quarantine\*.csv
```

</details>

To demonstrate bounded-memory processing, run the same input in small batches:

```bash
python -m src.pipeline \
  --input tests/fixtures/sample_dirty_data.csv \
  --chunk-size 2
```

The result should still be one accepted row and two rejected rows.

## Quick start with PostgreSQL

With Docker Desktop installed, start PostgreSQL and run the complete flow:

```bash
docker compose up -d postgres
export DATABASE_URL="postgresql+psycopg2://etl_user:etl_password@localhost:5432/etl_data_quality"

python -m src.pipeline \
  --input tests/fixtures/sample_dirty_data.csv \
  --load
```

<details>
<summary>Windows (PowerShell)</summary>

```powershell
docker compose up -d postgres
$env:DATABASE_URL = "postgresql+psycopg2://etl_user:etl_password@localhost:5432/etl_data_quality"

python -m src.pipeline `
  --input tests/fixtures/sample_dirty_data.csv `
  --load
```

</details>

The Compose initialization script creates the `empresas` and `quarantine`
tables automatically on first database startup. Re-run the load command: the
number of rows in `empresas` should not increase because the pipeline updates
an existing CNPJ instead of inserting a duplicate.

The credentials in `docker-compose.yml` are development-only defaults. Do not
reuse them in a shared or production environment.

## Usage

### CLI options

```text
--input PATH             Required input CSV
--load                   Persist valid and rejected rows in PostgreSQL
--chunk-size ROWS        Process large files in bounded batches
--quarantine-dir PATH    Destination for local quarantine CSV
--log-level LEVEL        DEBUG, INFO, WARNING, or ERROR
--log-file PATH          Optional JSON log file
```

Example for a large file:

```bash
python -m src.pipeline \
  --input data/raw/large-cnpj.csv \
  --chunk-size 10000 \
  --load \
  --log-file data/pipeline.log
```

<details>
<summary>Windows (PowerShell)</summary>

```powershell
python -m src.pipeline `
  --input data/raw/large-cnpj.csv `
  --chunk-size 10000 `
  --load `
  --log-file data/pipeline.log
```

</details>

### Data Quality API integration

Start the companion API according to its
[integrated demo](https://github.com/davimatosms/data-quality-api), then set
the URL and monitored source ID before running the ETL:

```bash
export QUALITY_API_URL="http://localhost:8000"
export QUALITY_API_SOURCE_ID="1"

python -m src.pipeline \
  --input tests/fixtures/sample_dirty_data.csv
```

<details>
<summary>Windows (PowerShell)</summary>

```powershell
$env:QUALITY_API_URL = "http://localhost:8000"
$env:QUALITY_API_SOURCE_ID = "1"

python -m src.pipeline `
  --input tests/fixtures/sample_dirty_data.csv
```

</details>

The current API contract uses Portuguese metric keys because the source
dataset is Brazilian: `linhas_lidas`, `linhas_validas`, `linhas_rejeitadas`,
and `tempo_segundos`. Brazilian domain identifiers such as `cnpj`,
`razao_social`, `cep`, and `empresas` remain unchanged as well.

### Output and observability

The command prints a JSON report containing the input copy and detected
encoding, row counts, rejection counts grouped by rule, database changes,
persisted quarantine count, elapsed time, and a transformed-data preview.
A representative report is:

```json
{
  "linhas_lidas": 3,
  "linhas_validas": 1,
  "linhas_rejeitadas": 2,
  "rejeicoes_por_regra": {
    "missing_cnpj": 1,
    "duplicate_cnpj": 1
  },
  "tempo_segundos": 0.123
}
```

Structured logs are written as one JSON object per line to `stderr`. They
include pipeline start and per-chunk processing events. Use `--log-file` to
persist them as UTF-8.

### Validation rules

The current implementation validates:

- CNPJ length, repeated-digit values, and check digits;
- required CNPJ and company name fields;
- CEP with eight digits;
- parseable activity dates;
- duplicate CNPJs within the same input;
- UTF-8 input with a controlled Latin-1 fallback.

Rejected rows include the source line number, original row content, one or
more rejection reasons, and the processing timestamp.

## Technical decisions

- **Quarantine instead of discard:** rejected data remains auditable and can
  be reprocessed after a rule or source issue is corrected.
- **Natural-key upsert:** CNPJ makes repeated execution idempotent and avoids
  truncate-and-reload behavior.
- **Pandas for the MVP:** it is familiar and sufficient for the educational
  scope. Chunked reads bound memory usage; Polars is a possible future
  performance experiment.
- **CLI instead of Airflow:** this project has no real users or scheduling
  requirement. Docker Compose plus GitHub Actions provide enough reproducible
  execution for the current scope.
- **Database initialization:** `sql/init.sql` is the source used by Docker
  and CI. The runtime calls the batch `upsert_empresas` PL/pgSQL function.

## Testing and quality

Run unit tests:

```bash
python -m pytest -q
```

Run integration tests against the local PostgreSQL container:

```bash
export TEST_DATABASE_URL="postgresql+psycopg2://etl_user:etl_password@localhost:5432/etl_data_quality"
python -m pytest -q
```

<details>
<summary>Windows (PowerShell)</summary>

```powershell
$env:TEST_DATABASE_URL = "postgresql+psycopg2://etl_user:etl_password@localhost:5432/etl_data_quality"
python -m pytest -q
```

</details>

The integration test is skipped when `TEST_DATABASE_URL` is not configured.
GitHub Actions starts PostgreSQL, initializes the schema, sets this variable,
and runs the full test suite. The CI quality gate requires 60% measured
coverage, Ruff, and Pyright.

The optional real-data demonstration fetches one company record from
BrasilAPI:

```bash
python scripts/fetch_real_cnpj_sample.py \
  --output data/raw/real_cnpj_sample.csv

python -m src.pipeline \
  --input data/raw/real_cnpj_sample.csv \
  --load
```

Raw files are intentionally not versioned.

## Project structure

```text
etl-data-quality/
├── .github/workflows/ci.yml       # Unit and PostgreSQL integration CI
├── data/
│   ├── raw/                       # Local inputs; ignored except fixtures
│   └── quarantine/                # Generated rejection files
├── docs/                          # Planning notes and original specification
├── scripts/
│   └── fetch_real_cnpj_sample.py # Small public-data demonstration
├── sql/
│   ├── init.sql                   # Database initialization
│   └── procedures/
│       └── upsert_empresa.sql     # PL/pgSQL reference implementation
├── src/
│   ├── db.py                      # SQLAlchemy engine creation
│   ├── extract.py                 # Raw copy, encoding, and chunk readers
│   ├── load.py                    # Data and quarantine persistence
│   ├── observability.py           # JSON logging
│   ├── pipeline.py                # CLI and orchestration
│   ├── quality_api.py             # Optional API reporting
│   ├── schemas.py                 # Shared schema constants/helpers
│   ├── transform.py               # Canonicalization
│   └── validate.py                # Data-quality rules
├── tests/
│   ├── fixtures/
│   │   └── sample_dirty_data.csv
│   ├── test_extract.py
│   ├── test_integration.py        # Runs when TEST_DATABASE_URL is set
│   ├── test_observability.py
│   ├── test_pipeline.py
│   ├── test_quality_api.py
│   └── test_validate.py
├── Dockerfile
├── docker-compose.yml
├── LICENSE
├── pyproject.toml
├── requirements.txt
└── README.md
```

Planning notes and the original specification live in [`docs/`](docs/).

## Known limitations and next steps

This repository is an academic MVP, not a production ingestion platform.
Known limitations and natural next steps are:

1. the input schema is fixed to the current CNPJ dataset layout;
2. there is no workflow orchestration or scheduling layer;
3. API reporting has no authentication mechanism yet;
4. each Pandas chunk is processed in memory, so larger workloads need a
   streaming or distributed processing strategy.

## Related projects

- [Data Quality API](https://github.com/davimatosms/data-quality-api) —
  tracks source checks, data freshness, and quality history.

## License

This project is released under the MIT License. See [LICENSE](LICENSE).
