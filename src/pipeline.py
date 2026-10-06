from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from src.db import create_database_engine, run_with_retry
from src.extract import (
    extract_raw_data,
    read_csv_chunks_with_encoding,
    read_csv_with_encoding,
)
from src.load import load_dataframe, load_quarantine
from src.observability import configure_logging
from src.quality_api import report_check_from_environment
from src.schemas import DataQualitySchema
from src.transform import normalize_dataframe
from src.validate import rejection_counts, validate_dataframe


def _write_quarantine(
    invalid_df: pd.DataFrame,
    source: Path,
    quarantine_dir: str | Path,
    output: Path | None = None,
) -> str | None:
    if invalid_df.empty:
        return None

    destination = Path(quarantine_dir)
    destination.mkdir(parents=True, exist_ok=True)
    output = output or destination / f"{source.stem}_quarantine.csv"
    invalid_df.to_csv(
        output,
        mode="a",
        header=not output.exists(),
        index=False,
        encoding="utf-8",
    )
    return str(output)


def _merge_load_reports(total: dict, current: dict) -> None:
    for key in ("upserted", "inserted", "updated", "rows"):
        total[key] += current.get(key, 0)


def run_pipeline(
    csv_path: str | Path,
    load_to_database: bool = False,
    quarantine_dir: str | Path = "data/quarantine",
    chunk_size: int | None = None,
    logger=None,
) -> dict:
    started_at = time.perf_counter()
    source = Path(csv_path)
    raw_file = extract_raw_data(source)
    if chunk_size is not None and chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    load_report = {"upserted": 0, "inserted": 0, "updated": 0, "rows": 0}
    quarantine_loaded = 0
    rows_read = 0
    valid_count = 0
    rejected_count = 0
    preview: list[dict] = []
    seen_cnpjs: set[str] = set()
    quarantine_file: str | None = None
    quarantine_output = Path(quarantine_dir) / (
        f"{source.stem}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S_%f')}_quarantine.csv"
    )
    engine = create_database_engine() if load_to_database else None
    rejection_metrics: dict[str, int] = {}

    if chunk_size is None:
        dataframe, encoding = read_csv_with_encoding(raw_file)
        DataQualitySchema.validate_columns(list(dataframe.columns))
        chunks = [(dataframe, 0)]
    else:
        chunk_iterator, encoding = read_csv_chunks_with_encoding(raw_file, chunk_size)
        chunks = ((chunk, offset) for offset, chunk in enumerate(chunk_iterator))

    for chunk_number, (df, chunk_index) in enumerate(chunks):
        if chunk_number == 0:
            DataQualitySchema.validate_columns(list(df.columns))
        line_offset = chunk_index * chunk_size if chunk_size else 0
        valid_df, invalid_df = validate_dataframe(
            df,
            line_offset=line_offset,
            seen_cnpjs=seen_cnpjs,
        )
        normalized_df = normalize_dataframe(valid_df)
        current_quarantine_file = _write_quarantine(
            invalid_df,
            source,
            quarantine_dir,
            quarantine_output,
        )
        if current_quarantine_file:
            quarantine_file = current_quarantine_file

        rows_read += len(df)
        valid_count += len(valid_df)
        rejected_count += len(invalid_df)
        for reason, count in rejection_counts(invalid_df).items():
            rejection_metrics[reason] = rejection_metrics.get(reason, 0) + count
        preview.extend(normalized_df.head(max(0, 5 - len(preview))).to_dict(orient="records"))
        if logger:
            logger.info(
                "chunk_processed",
                extra={
                    "chunk_number": chunk_number,
                    "rows": len(df),
                    "valid": len(valid_df),
                    "rejected": len(invalid_df),
                },
            )

        if engine is not None:
            _merge_load_reports(
                load_report,
                run_with_retry(
                    engine,
                    lambda connection, dataframe=normalized_df: load_dataframe(
                        dataframe, connection
                    ),
                ),
            )
            quarantine_loaded += run_with_retry(
                engine,
                lambda connection, dataframe=invalid_df: load_quarantine(
                    dataframe,
                    connection,
                    str(raw_file),
                ),
            )

    report = {
        "raw_file": raw_file,
        "quarantine_file": quarantine_file,
        "encoding": encoding,
        "linhas_lidas": rows_read,
        "linhas_validas": valid_count,
        "linhas_rejeitadas": rejected_count,
        "rejeicoes_por_regra": rejection_metrics,
        "carga": load_report,
        "quarantine_carregada": quarantine_loaded,
        "tempo_segundos": round(time.perf_counter() - started_at, 3),
        "dataset_transformado": preview,
    }
    api_response = report_check_from_environment(report)
    if api_response is not None:
        report["quality_api"] = api_response
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the ETL data quality pipeline.")
    parser.add_argument("--input", required=True, help="Input CSV path.")
    parser.add_argument(
        "--load",
        action="store_true",
        help="Load valid and rejected rows into PostgreSQL.",
    )
    parser.add_argument("--quarantine-dir", default="data/quarantine")
    parser.add_argument("--chunk-size", type=int, help="Rows per batch for large CSV files.")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
    )
    parser.add_argument("--log-file", help="Optional JSON log file path.")
    args = parser.parse_args()
    logger = configure_logging(args.log_level, args.log_file)
    logger.info("pipeline_started", extra={"input": args.input, "load": args.load})
    print(json.dumps(
        run_pipeline(args.input, args.load, args.quarantine_dir, args.chunk_size, logger),
        ensure_ascii=False,
        indent=2,
    ))


if __name__ == "__main__":
    main()
