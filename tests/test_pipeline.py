from pathlib import Path

import pytest

from src.pipeline import run_pipeline

FIXTURE = Path(__file__).parent / "fixtures" / "sample_dirty_data.csv"


def test_pipeline_creates_report_and_quarantine(tmp_path: Path) -> None:
    report = run_pipeline(FIXTURE, quarantine_dir=tmp_path)

    assert report["linhas_lidas"] == 3
    assert report["linhas_validas"] == 1
    assert report["linhas_rejeitadas"] == 2
    assert report["quarantine_file"] is not None


def test_pipeline_supports_chunks(tmp_path: Path) -> None:
    report = run_pipeline(FIXTURE, quarantine_dir=tmp_path, chunk_size=2)

    assert report["linhas_lidas"] == 3
    assert report["linhas_validas"] == 1
    assert report["linhas_rejeitadas"] == 2
    assert report["rejeicoes_por_regra"]


def test_pipeline_rejects_invalid_chunk_size() -> None:
    with pytest.raises(ValueError, match="chunk_size"):
        run_pipeline(FIXTURE, chunk_size=0)


def test_pipeline_rejects_missing_columns(tmp_path: Path) -> None:
    source = tmp_path / "missing.csv"
    source.write_text("cnpj\n123\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Missing required columns"):
        run_pipeline(source, quarantine_dir=tmp_path)
