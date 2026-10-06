from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

from src.pipeline import run_pipeline


def create_source(api_url: str) -> int:
    payload = json.dumps(
        {
            "name": "empresas-demo",
            "description": "Fonte criada pelo demo integrado",
            "expected_frequency_minutes": 1440,
            "freshness_tolerance": 1.5,
            "quality_rules": ["cnpj_duplicado", "cnpj_vazio"],
        }
    ).encode("utf-8")
    request = Request(
        f"{api_url.rstrip('/')}/sources",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=10) as response:
        return json.loads(response.read())["id"]


def main() -> None:
    api_url = os.environ["QUALITY_API_URL"]
    source_id = create_source(api_url)
    os.environ["QUALITY_API_SOURCE_ID"] = str(source_id)
    report = run_pipeline(
        Path("tests/fixtures/sample_dirty_data.csv"),
        load_to_database=True,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
