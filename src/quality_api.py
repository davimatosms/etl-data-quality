from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class QualityApiError(RuntimeError):
    """Raised when a quality check cannot be reported."""


def report_check(
    report: dict,
    *,
    api_url: str,
    source_id: int,
    timeout: float = 5.0,
    retries: int = 2,
) -> dict:
    rejected = report["linhas_rejeitadas"]
    payload = {
        "checked_at": datetime.now(UTC).isoformat(),
        "status": "PASSING" if rejected == 0 else "FAILING",
        "rule_results": [
            {
                "rule_name": rule,
                "passed": count == 0,
                "message": f"{count} linha(s) rejeitada(s)" if count else None,
            }
            for rule, count in report["rejeicoes_por_regra"].items()
        ],
        "metrics": {
            "linhas_lidas": report["linhas_lidas"],
            "linhas_validas": report["linhas_validas"],
            "linhas_rejeitadas": rejected,
            "rejeicoes_por_regra": report["rejeicoes_por_regra"],
            "tempo_segundos": report["tempo_segundos"],
        },
    }
    endpoint = f"{api_url.rstrip('/')}/sources/{source_id}/checks"
    request = Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError) as error:
            last_error = error
            if attempt < retries:
                time.sleep(0.2 * (attempt + 1))
    raise QualityApiError(f"Failed to report check to {endpoint}") from last_error


def report_check_from_environment(report: dict) -> dict | None:
    api_url = os.getenv("QUALITY_API_URL")
    source_id = os.getenv("QUALITY_API_SOURCE_ID")
    if not api_url and not source_id:
        return None
    if not api_url or not source_id:
        raise QualityApiError("QUALITY_API_URL and QUALITY_API_SOURCE_ID must be set together")
    try:
        parsed_source_id = int(source_id)
    except ValueError as error:
        raise QualityApiError("QUALITY_API_SOURCE_ID must be an integer") from error
    return report_check(report, api_url=api_url, source_id=parsed_source_id)
