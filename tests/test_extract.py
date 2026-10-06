from pathlib import Path

from src.extract import read_csv_chunks_with_encoding, read_csv_with_encoding


def test_read_csv_with_encoding_falls_back_to_latin1(tmp_path: Path):
    source = tmp_path / "latin1.csv"
    source.write_bytes("cnpj;razao_social\n04252011000110;Razão Social\n".encode("latin-1"))

    dataframe, encoding = read_csv_with_encoding(source)

    assert encoding == "latin-1"
    assert dataframe["razao_social"].iloc[0] == "Razão Social"


def test_read_csv_chunks_preserves_all_rows(tmp_path: Path):
    source = tmp_path / "sample.csv"
    source.write_text(
        "cnpj;razao_social\n"
        "04252011000110;Empresa A\n"
        "11222333000181;Empresa B\n",
        encoding="utf-8",
    )

    chunks, encoding = read_csv_chunks_with_encoding(source, chunksize=1)

    assert encoding == "utf-8"
    assert sum(len(chunk) for chunk in chunks) == 2
