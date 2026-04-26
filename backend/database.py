from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_reference TEXT NOT NULL,
                run_type TEXT NOT NULL,
                run_id TEXT NOT NULL,
                batch_id TEXT,
                predicted_gender TEXT,
                predicted_sleeve TEXT,
                gender_confidence REAL,
                sleeve_confidence REAL,
                model_name TEXT NOT NULL,
                model_version TEXT NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def insert_prediction(db_path: Path, row: dict[str, Any]) -> None:
    now_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload = {
        "image_reference": row.get("image_reference"),
        "run_type": row.get("run_type"),
        "run_id": row.get("run_id"),
        "batch_id": row.get("batch_id"),
        "predicted_gender": row.get("predicted_gender"),
        "predicted_sleeve": row.get("predicted_sleeve"),
        "gender_confidence": row.get("gender_confidence"),
        "sleeve_confidence": row.get("sleeve_confidence"),
        "model_name": row.get("model_name"),
        "model_version": row.get("model_version"),
        "status": row.get("status"),
        "error_message": row.get("error_message"),
        "created_at": row.get("created_at", now_utc),
    }

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO predictions (
                image_reference, run_type, run_id, batch_id,
                predicted_gender, predicted_sleeve, gender_confidence, sleeve_confidence,
                model_name, model_version, status, error_message, created_at
            ) VALUES (
                :image_reference, :run_type, :run_id, :batch_id,
                :predicted_gender, :predicted_sleeve, :gender_confidence, :sleeve_confidence,
                :model_name, :model_version, :status, :error_message, :created_at
            )
            """,
            payload,
        )
        conn.commit()


def list_predictions(db_path: Path, limit: int = 100) -> list[dict[str, Any]]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT *
            FROM predictions
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]
