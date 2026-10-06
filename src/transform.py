from __future__ import annotations

import re

import pandas as pd


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply a basic normalization pass to valid rows."""
    if df.empty:
        return df.copy()

    normalized = df.copy()
    if "cnpj" in normalized.columns:
        normalized["cnpj"] = normalized["cnpj"].map(
            lambda value: re.sub(r"\D", "", str(value))
        )

    for column in ["cnpj", "razao_social", "uf", "municipio"]:
        if column in normalized.columns:
            normalized[column] = normalized[column].astype(str).str.strip()

    if "data_inicio_atividade" in normalized.columns:
        normalized["data_inicio_atividade"] = pd.to_datetime(
            normalized["data_inicio_atividade"], errors="coerce"
        ).dt.strftime("%Y-%m-%d")

    return normalized
