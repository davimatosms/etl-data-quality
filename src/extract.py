from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd


def extract_raw_data(source_path: str | Path, destination_dir: str | Path = "data/raw") -> str:
    """Copy a raw data file to a timestamped raw directory without overwriting previous files."""
    source = Path(source_path)
    destination = Path(destination_dir)
    destination.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")
    target_path = destination / f"{source.stem}_{timestamp}{source.suffix}"
    target_path.write_bytes(source.read_bytes())

    return str(target_path)


def read_csv_with_encoding(
    source_path: str | Path,
    separator: str = ";",
) -> tuple[pd.DataFrame, str]:
    """Read a CSV using UTF-8 first and Latin-1 as a controlled fallback."""
    source = Path(source_path)
    errors: list[str] = []
    for encoding in ("utf-8", "latin-1"):
        try:
            return (
                pd.read_csv(
                    source,
                    sep=separator,
                    dtype=str,
                    keep_default_na=False,
                    encoding=encoding,
                ),
                encoding,
            )
        except UnicodeDecodeError as error:
            errors.append(f"{encoding}: {error}")
    raise UnicodeError("Unable to decode CSV with supported encodings: " + "; ".join(errors))


def read_csv_chunks_with_encoding(
    source_path: str | Path,
    chunksize: int,
    separator: str = ";",
) -> tuple[Iterator[pd.DataFrame], str]:
    """Return a chunk iterator after detecting a supported CSV encoding."""
    source = Path(source_path)
    for encoding in ("utf-8", "latin-1"):
        try:
            pd.read_csv(
                source,
                sep=separator,
                dtype=str,
                keep_default_na=False,
                encoding=encoding,
                nrows=1,
            )
            return (
                pd.read_csv(
                    source,
                    sep=separator,
                    dtype=str,
                    keep_default_na=False,
                    encoding=encoding,
                    chunksize=chunksize,
                ),
                encoding,
            )
        except UnicodeDecodeError:
            continue
    raise UnicodeError("Unable to decode CSV with supported encodings: utf-8, latin-1")
