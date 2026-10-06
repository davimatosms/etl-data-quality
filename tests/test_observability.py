import json
import logging

from src.observability import JsonFormatter


def test_json_formatter_emits_structured_log():
    record = logging.LogRecord(
        name="etl_data_quality",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="chunk_processed",
        args=(),
        exc_info=None,
    )

    payload = json.loads(JsonFormatter().format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "etl_data_quality"
    assert payload["message"] == "chunk_processed"
    assert "timestamp" in payload
