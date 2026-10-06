from __future__ import annotations

import re
from collections import Counter

import pandas as pd


def _digits(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return re.sub(r"\D", "", str(value))


def is_valid_cnpj(value: object) -> bool:
    """Validate a Brazilian CNPJ, including both check digits."""
    cnpj = _digits(value)
    if len(cnpj) != 14 or len(set(cnpj)) == 1:
        return False

    weights_first = (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
    total = sum(
        int(digit) * weight for digit, weight in zip(cnpj[:12], weights_first, strict=True)
    )
    first_digit = 0 if total % 11 < 2 else 11 - (total % 11)

    weights_second = (6,) + weights_first
    total = sum(
        int(digit) * weight
        for digit, weight in zip(cnpj[:13], weights_second, strict=True)
    )
    second_digit = 0 if total % 11 < 2 else 11 - (total % 11)

    return cnpj[-2:] == f"{first_digit}{second_digit}"


def _is_valid_date(value: object) -> bool:
    if value is None or (isinstance(value, float) and pd.isna(value)) or str(value).strip() == "":
        return True
    return not pd.isna(pd.to_datetime(str(value), errors="coerce", dayfirst=False))


def _is_valid_cep(value: object) -> bool:
    cep = _digits(value)
    return len(cep) == 8


def validate_dataframe(
    df: pd.DataFrame,
    line_offset: int = 0,
    seen_cnpjs: set[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split valid rows from invalid rows and record every rejection reason."""
    if df.empty:
        return df.copy(), df.copy()

    valid_rows = []
    invalid_rows = []
    seen = seen_cnpjs if seen_cnpjs is not None else set()

    for index, row in df.iterrows():
        reasons: list[str] = []
        cnpj = _digits(row.get("cnpj"))
        if not cnpj:
            reasons.append("cnpj_vazio")
        elif not is_valid_cnpj(cnpj):
            reasons.append("cnpj_invalido")
        elif cnpj in seen:
            reasons.append("cnpj_duplicado")
        else:
            seen.add(cnpj)

        razao_social = row.get("razao_social")
        if razao_social is None or str(razao_social).strip() == "":
            reasons.append("razao_social_vazia")
        if "cep" in row and not _is_valid_cep(row.get("cep")):
            reasons.append("cep_invalido")
        if "data_inicio_atividade" in row and not _is_valid_date(row.get("data_inicio_atividade")):
            reasons.append("data_inicio_atividade_invalida")

        if reasons:
            invalid_rows.append({
                "numero_linha": int(str(index)) + line_offset + 2,
                "linha_original": row.to_dict(),
                "motivo_rejeicao": ";".join(reasons),
                "timestamp_processamento": pd.Timestamp.utcnow().isoformat(),
            })
        else:
            valid_rows.append(row.to_dict())

    valid_df = pd.DataFrame(valid_rows)
    invalid_df = pd.DataFrame(invalid_rows)
    return valid_df, invalid_df


def rejection_counts(invalid_df: pd.DataFrame) -> dict[str, int]:
    """Count each rejection rule, including rows with multiple violations."""
    if invalid_df.empty:
        return {}

    counts: Counter[str] = Counter()
    for reasons in invalid_df["motivo_rejeicao"]:
        counts.update(str(reasons).split(";"))
    return dict(sorted(counts.items()))
