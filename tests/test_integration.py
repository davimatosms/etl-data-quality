import os

import pandas as pd
import pytest
from sqlalchemy import create_engine, text

from src.load import load_dataframe, load_quarantine

DATABASE_URL = os.getenv("TEST_DATABASE_URL")


@pytest.mark.skipif(not DATABASE_URL, reason="TEST_DATABASE_URL is not configured")
def test_database_load_is_idempotent_and_persists_quarantine():
    engine = create_engine(DATABASE_URL)
    valid = pd.DataFrame(
        [{
            "cnpj": "04252011000110",
            "razao_social": "Empresa Integração",
            "data_inicio_atividade": "2020-01-15",
            "cep": "01000000",
            "uf": "SP",
            "municipio": "São Paulo",
        }]
    )
    invalid = pd.DataFrame(
        [{
            "numero_linha": 3,
            "linha_original": {"cnpj": ""},
            "motivo_rejeicao": "cnpj_vazio",
        }]
    )

    with engine.connect() as connection:
        connection.execute(text("TRUNCATE empresas, quarantine RESTART IDENTITY"))
        connection.commit()
        load_dataframe(valid, connection)
        load_dataframe(valid, connection)
        load_quarantine(invalid, connection, "sample.csv")
        counts = connection.execute(
            text("SELECT (SELECT COUNT(*) FROM empresas), (SELECT COUNT(*) FROM quarantine)")
        ).one()

    assert counts == (1, 1)
