import json
from urllib.request import Request

import pytest

from src.quality_api import QualityApiError, report_check, report_check_from_environment

REPORT = {
    "linhas_lidas": 3,
    "linhas_validas": 1,
    "linhas_rejeitadas": 2,
    "rejeicoes_por_regra": {"cnpj": 2},
    "tempo_segundos": 0.1,
}


def test_report_check_sends_contract(monkeypatch):
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'{"id": 10}'

    def fake_urlopen(request: Request, timeout: float):
        captured["url"] = request.full_url
        captured["payload"] = json.loads(request.data)
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr("src.quality_api.urlopen", fake_urlopen)
    result = report_check(REPORT, api_url="http://api:8000", source_id=4)

    assert result == {"id": 10}
    assert captured["url"] == "http://api:8000/sources/4/checks"
    assert captured["payload"]["status"] == "FAILING"
    assert captured["payload"]["rule_results"][0]["rule_name"] == "cnpj"


def test_environment_report_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("QUALITY_API_URL", raising=False)
    monkeypatch.delenv("QUALITY_API_SOURCE_ID", raising=False)
    assert report_check_from_environment(REPORT) is None


def test_environment_requires_both_values(monkeypatch):
    monkeypatch.setenv("QUALITY_API_URL", "http://api:8000")
    monkeypatch.delenv("QUALITY_API_SOURCE_ID", raising=False)
    with pytest.raises(QualityApiError, match="must be set together"):
        report_check_from_environment(REPORT)
