from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy import text


def load_dataframe(df: pd.DataFrame, connection: Any) -> dict[str, Any]:
    """Persist valid rows with a single transactional batch upsert."""
    if df.empty:
        return {"upserted": 0, "inserted": 0, "updated": 0, "rows": 0}

    rows = df.to_dict(orient="records")
    statement = text("SELECT * FROM upsert_empresas(CAST(:rows AS JSONB))")
    import json
    with connection.begin():
        result = connection.execute(
            statement,
            {"rows": json.dumps(rows, ensure_ascii=False)},
        ).mappings().one()

    return {
        "upserted": len(rows),
        "inserted": result["inserted_count"],
        "updated": result["updated_count"],
        "rows": len(rows),
    }


def load_quarantine(
    invalid_df: pd.DataFrame,
    connection: Any,
    source_file: str,
) -> int:
    """Persist rejected rows in the quarantine table."""
    if invalid_df.empty:
        return 0

    rows = [
        {
            "source_file": source_file,
            "row_number": int(record.get("numero_linha", 0)),
            "raw_line": record.get("linha_original", {}),
            "rejection_reason": record["motivo_rejeicao"],
        }
        for record in invalid_df.to_dict(orient="records")
    ]
    statement = text(
        """
        INSERT INTO quarantine (
            source_file, row_number, raw_line, rejection_reason
        )
        VALUES (
            :source_file, :row_number, CAST(:raw_line AS JSONB), :rejection_reason
        )
        """
    )
    import json

    for row in rows:
        row["raw_line"] = json.dumps(row["raw_line"], ensure_ascii=False)
    with connection.begin():
        connection.execute(statement, rows)
    return len(rows)
