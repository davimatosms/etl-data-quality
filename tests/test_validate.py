import pandas as pd
import pytest

from src.load import load_dataframe
from src.schemas import DataQualitySchema
from src.transform import normalize_dataframe
from src.validate import rejection_counts, validate_dataframe


def test_validate_dataframe_keeps_valid_rows():
    df = pd.DataFrame([
        {"cnpj": "04.252.011/0001-10", "razao_social": "Empresa Teste"},
    ])

    valid_df, invalid_df = validate_dataframe(df)

    assert len(valid_df) == 1
    assert invalid_df.empty


def test_validate_dataframe_rejects_empty_required_fields():
    df = pd.DataFrame([
        {"cnpj": "", "razao_social": ""},
    ])

    valid_df, invalid_df = validate_dataframe(df)

    assert valid_df.empty
    assert len(invalid_df) == 1
    assert "cnpj_vazio" in invalid_df["motivo_rejeicao"].iloc[0]


def test_validate_dataframe_rejects_invalid_cnpj():
    df = pd.DataFrame([
        {"cnpj": "04.252.011/0001-11", "razao_social": "Empresa Teste"},
    ])

    valid_df, invalid_df = validate_dataframe(df)

    assert valid_df.empty
    assert "cnpj_invalido" in invalid_df["motivo_rejeicao"].iloc[0]


def test_validate_dataframe_rejects_duplicate_cnpj():
    df = pd.DataFrame([
        {"cnpj": "04.252.011/0001-10", "razao_social": "Empresa A"},
        {"cnpj": "04.252.011/0001-10", "razao_social": "Empresa B"},
    ])

    valid_df, invalid_df = validate_dataframe(df)

    assert len(valid_df) == 1
    assert "cnpj_duplicado" in invalid_df["motivo_rejeicao"].iloc[0]


def test_validate_dataframe_rejects_invalid_cep_and_date():
    df = pd.DataFrame([
        {
            "cnpj": "04.252.011/0001-10",
            "razao_social": "Empresa Teste",
            "cep": "123",
            "data_inicio_atividade": "data-invalida",
        },
    ])

    valid_df, invalid_df = validate_dataframe(df)

    assert valid_df.empty
    reasons = invalid_df["motivo_rejeicao"].iloc[0]
    assert "cep_invalido" in reasons
    assert "data_inicio_atividade_invalida" in reasons


def test_load_dataframe_returns_zero_for_empty_input():
    result = load_dataframe(pd.DataFrame(), connection=None)

    assert result == {"upserted": 0, "inserted": 0, "updated": 0, "rows": 0}


def test_normalize_dataframe_removes_cnpj_mask():
    df = pd.DataFrame([{"cnpj": "04.252.011/0001-10"}])

    normalized = normalize_dataframe(df)

    assert normalized["cnpj"].iloc[0] == "04252011000110"


def test_validation_line_offset_preserves_source_line_number():
    df = pd.DataFrame([{"cnpj": "", "razao_social": "Empresa"}])

    _, invalid_df = validate_dataframe(df, line_offset=10)

    assert invalid_df["numero_linha"].iloc[0] == 12


def test_rejection_counts_include_multiple_reasons_per_row():
    df = pd.DataFrame(
        [
            {"motivo_rejeicao": "cnpj_vazio;cep_invalido"},
            {"motivo_rejeicao": "cep_invalido"},
        ]
    )

    assert rejection_counts(df) == {"cep_invalido": 2, "cnpj_vazio": 1}


def test_schema_rejects_missing_required_columns():
    with pytest.raises(ValueError, match="razao_social"):
        DataQualitySchema.validate_columns(["cnpj"])
