# ETL Data Quality

An educational ETL pipeline for validating, transforming, and loading
Brazilian public data into PostgreSQL.

The project is intentionally small enough to run locally, but demonstrates
production-oriented practices:

- explicit data-quality rules;
- rejection quarantine instead of silent data loss;
- idempotent upserts using a natural key;
- bounded-memory CSV processing;
- structured JSON logs and operational metrics;
- unit and PostgreSQL integration tests;
- Docker-based local development and GitHub Actions CI.

## Problem statement

Public datasets commonly contain malformed identifiers, inconsistent
encodings, missing fields, invalid dates, duplicated records, and
inconsistent types. Loading these values without validation can silently
corrupt downstream analysis.

This pipeline keeps the raw input, validates each row, records rejected rows
with their reasons, transforms accepted rows, and loads only accepted data
into PostgreSQL.

## Architecture

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

The default execution is a CLI-driven pipeline. PostgreSQL is the only
required service for database-backed execution; workflow orchestration tools
are intentionally out of scope for this academic MVP.

## Data Quality API integration

After a run, the pipeline can report its result to the companion
[Data Quality API](https://github.com/davimatosms/data-quality-api). Set both
variables to enable it:

```powershell
$env:QUALITY_API_URL = "http://localhost:8000"
$env:QUALITY_API_SOURCE_ID = "1"
python -m src.pipeline --input tests/fixtures/sample_dirty_data.csv
```

The ETL remains responsible for validation. It sends the API the execution
timestamp, `PASSING`/`FAILING` status, per-rule results, and metrics. Requests
use a timeout and retry transient network failures. If the variables are not
set, the pipeline behaves as before and only prints its local report.

## What should I do with this project?

If you downloaded this repository and do not know ETL yet, think of it as a
quality-checking machine for a CSV file containing Brazilian company data.

You give it a CSV. It:

1. reads the file;
2. checks each company record;
3. separates accepted and rejected rows;
4. normalizes accepted values, such as removing CNPJ punctuation;
5. saves rejected rows with the reason for rejection;
6. optionally stores the accepted data in PostgreSQL.

You do not need to create a CSV to try it. The repository includes a small
intentionally problematic sample at
`tests/fixtures/sample_dirty_data.csv`.

### First try: run it without a database

From the repository folder, install Python dependencies and run:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

python -m src.pipeline `
  --input tests/fixtures/sample_dirty_data.csv
```

The command prints a JSON report. The sample has three rows:

- one valid company;
- one row without a CNPJ;
- one duplicate CNPJ.

Therefore, you should see three rows read, one accepted, and two rejected.
The accepted CNPJ is shown in canonical form, without punctuation. The
rejected rows are written to a CSV file under `data/quarantine/`.

Inspect the generated quarantine file with:

```powershell
Get-ChildItem data\quarantine
Get-Content data\quarantine\*.csv
```

This is the easiest way to see the project's main behavior: invalid data is
not silently discarded and does not enter the valid dataset.

### Try the same file in small batches

```powershell
python -m src.pipeline `
  --input tests/fixtures/sample_dirty_data.csv `
  --chunk-size 2
```

The result should still be one accepted row and two rejected rows. This
demonstrates that the pipeline can process larger files in bounded batches.

### Try the database-backed version

If Docker Desktop is installed, start PostgreSQL and run the complete flow:

```powershell
docker compose up -d postgres

$env:DATABASE_URL = "postgresql+psycopg2://etl_user:etl_password@localhost:5432/etl_data_quality"

python -m src.pipeline `
  --input tests/fixtures/sample_dirty_data.csv `
  --load
```

The accepted company is stored in the `empresas` table. Rejected rows are
also stored in the `quarantine` table. To inspect them:

```powershell
docker compose exec -T postgres psql `
  -U etl_user `
  -d etl_data_quality `
  -c "SELECT cnpj, razao_social, uf FROM empresas;"

docker compose exec -T postgres psql `
  -U etl_user `
  -d etl_data_quality `
  -c "SELECT source_file, row_data FROM quarantine;"
```

Run the load command a second time. The number of rows in `empresas` should
not increase because the pipeline updates an existing CNPJ instead of
inserting a duplicate. This is the project's idempotency behavior.

## Validation rules

The current implementation validates:

- CNPJ length, repeated-digit values, and check digits;
- required CNPJ and company name fields;
- CEP with eight digits;
- parseable activity dates;
- duplicate CNPJs within the same input;
- UTF-8 input with a controlled Latin-1 fallback.

Rejected rows include:

- source line number;
- original row content;
- one or more rejection reasons;
- processing timestamp.

## Repository layout

```text
etl-data-quality/
├── .github/workflows/ci.yml       # Unit and PostgreSQL integration CI
├── data/
│   ├── raw/                       # Local inputs; ignored except fixtures
│   └── quarantine/                # Generated rejection files
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
│   ├── schemas.py                 # Shared schema constants/helpers
│   ├── transform.py               # Canonicalization
│   └── validate.py                # Data-quality rules
├── tests/
│   ├── fixtures/
│   │   └── realistic_cnpj_sample.csv
│   ├── test_extract.py
│   ├── test_integration.py        # Runs when TEST_DATABASE_URL is set
│   ├── test_observability.py
│   └── test_validate.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.12 or newer;
- Docker Desktop and Docker Compose;
- PostgreSQL 16 when running without Docker;
- network access only when using the optional public-data sample script.

## Quick start

Create and activate a virtual environment, then install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Start PostgreSQL:

```powershell
docker compose up -d postgres
```

Run validation and transformation without database loading:

```powershell
python -m src.pipeline `
  --input tests/fixtures/sample_dirty_data.csv
```

Run the complete pipeline with PostgreSQL:

```powershell
$env:DATABASE_URL = "postgresql+psycopg2://etl_user:etl_password@localhost:5432/etl_data_quality"

python -m src.pipeline `
  --input tests/fixtures/sample_dirty_data.csv `
  --load
```

The Compose initialization script creates the `empresas` and `quarantine`
tables automatically on first database startup.

> The credentials in `docker-compose.yml` are development-only defaults. Do
> not reuse them in a shared or production environment.

## CLI options

```text
--input PATH             Required input CSV
--load                   Persist valid and rejected rows in PostgreSQL
--chunk-size ROWS        Process large files in bounded batches
--quarantine-dir PATH    Destination for local quarantine CSV
--log-level LEVEL        DEBUG, INFO, WARNING, or ERROR
--log-file PATH          Optional JSON log file
```

Example for a large file:

```powershell
python -m src.pipeline `
  --input data/raw/large-cnpj.csv `
  --chunk-size 10000 `
  --load `
  --log-file data/pipeline.log
```

## Output and observability

The command prints a JSON report containing:

- input copy and detected encoding;
- rows read, accepted, and rejected;
- rejection counts grouped by rule;
- inserted and updated database rows;
- persisted quarantine count;
- elapsed time;
- a small transformed-data preview.

Structured logs are written as one JSON object per line to `stderr`. They
include pipeline start and per-chunk processing events. Use `--log-file` to
persist them as UTF-8.

## Testing

Run unit tests:

```powershell
python -m pytest -q
```

Run integration tests against the local PostgreSQL container:

```powershell
$env:TEST_DATABASE_URL = "postgresql+psycopg2://etl_user:etl_password@localhost:5432/etl_data_quality"
python -m pytest -q
```

The integration test is skipped when `TEST_DATABASE_URL` is not configured.
GitHub Actions starts PostgreSQL, initializes the schema, sets this variable,
and runs the full test suite.

## Real-data demonstration

The optional script fetches one real company record from BrasilAPI and writes a
small compatible CSV:

```powershell
python scripts/fetch_real_cnpj_sample.py `
  --output data/raw/real_cnpj_sample.csv

python -m src.pipeline `
  --input data/raw/real_cnpj_sample.csv `
  --load
```

This is a small demonstration, not a replacement for downloading the official
large Receita Federal datasets. Raw files are intentionally not versioned.

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
- **Database initialization:** `sql/init.sql` is the source used by Docker and
  the CI environment. The runtime calls the batch `upsert_empresas` PL/pgSQL
  function defined in that schema.

## Known limitations and next improvements

This repository is an academic MVP, not a production ingestion platform. The
most relevant follow-up work is:

1. add configurable source schemas for datasets other than the sample CNPJ
   layout;
2. add retention and partitioning policies for large quarantine tables.

## License

This project is released under the MIT License. See `LICENSE`.

The CI quality gate requires 60% measured coverage, Ruff, and Pyright. The
database engine module is excluded from the coverage threshold because its
behavior is exercised through the integration environment.
