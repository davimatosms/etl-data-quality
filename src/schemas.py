from __future__ import annotations

from typing import Any


class DataQualitySchema:
    """Schema base used by validation and transform layers."""

    REQUIRED_COLUMNS = [
        "cnpj",
        "razao_social",
        "data_inicio_atividade",
        "cep",
        "uf",
    ]

    @classmethod
    def validate_columns(cls, columns: list[str]) -> list[str]:
        missing = [column for column in cls.REQUIRED_COLUMNS if column not in columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        return columns

    @staticmethod
    def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(row)
        for key, value in normalized.items():
            if isinstance(value, str):
                normalized[key] = value.strip()
        return normalized
