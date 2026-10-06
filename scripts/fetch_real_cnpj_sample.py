from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import TypedDict
from urllib.request import Request, urlopen

API_URL = "https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
SAMPLE_CNPJS = ("04252011000110",)
FIELDS = (
    "cnpj",
    "razao_social",
    "data_inicio_atividade",
    "cep",
    "uf",
    "municipio",
)

class CompanyRow(TypedDict):
    cnpj: str
    razao_social: str
    data_inicio_atividade: str
    cep: str
    uf: str
    municipio: str


def fetch_company(cnpj: str) -> CompanyRow:
    request = Request(
        API_URL.format(cnpj=cnpj),
        headers={"User-Agent": "etl-data-quality/0.1"},
    )
    with urlopen(request, timeout=30) as response:
        payload = json.load(response)
    return {field: str(payload.get(field) or "") for field in FIELDS}  # type: ignore


def main() -> None:
    parser = argparse.ArgumentParser(description="Download a small real CNPJ sample.")
    parser.add_argument("--output", default="data/raw/real_cnpj_sample.csv")
    args = parser.parse_args()

    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    rows = [fetch_company(cnpj) for cnpj in SAMPLE_CNPJS]
    with destination.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)  # pyright: ignore[reportArgumentType]
    print(f"Saved {len(rows)} real records to {destination}")


if __name__ == "__main__":
    main()
