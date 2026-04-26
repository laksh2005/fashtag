from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.catalog import list_products
from backend.database import init_db, insert_prediction, list_predictions
from backend.inference import ModelPredictor
from backend.schemas import PredictBatchRequest, PredictSingleRequest
from backend.settings import (
    METADATA_CSV,
    PREDICTIONS_DB,
    RAW_IMAGE_DIR,
    resolve_checkpoint_path,
)

app = FastAPI(title="FashTag API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

predictor: ModelPredictor | None = None


def get_predictor() -> ModelPredictor:
    if predictor is None:
        raise HTTPException(status_code=500, detail="Model predictor is not initialized.")
    return predictor


def log_prediction(row: dict[str, Any]) -> None:
    insert_prediction(PREDICTIONS_DB, row)


@app.on_event("startup")
def on_startup() -> None:
    global predictor
    init_db(PREDICTIONS_DB)
    checkpoint_path = resolve_checkpoint_path()
    predictor = ModelPredictor(checkpoint_path=checkpoint_path)

    RAW_IMAGE_DIR.mkdir(parents=True, exist_ok=True)


app.mount("/assets", StaticFiles(directory=str(RAW_IMAGE_DIR)), name="assets")


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "service": "FashTag API", "ui": "http://127.0.0.1:3000"}


@app.get("/health")
def health() -> dict[str, str]:
    model = get_predictor()
    return {"status": "ok", "model_name": model.model_name, "model_version": model.model_version}


@app.get("/products")
def products(
    limit: int = Query(60, ge=1, le=500),
    offset: int = Query(0, ge=0),
    class_name: str | None = None,
) -> list[dict[str, Any]]:
    return list_products(METADATA_CSV, limit=limit, offset=offset, class_name=class_name)


@app.post("/predict-single")
def predict_single(payload: PredictSingleRequest) -> dict[str, Any]:
    model = get_predictor()
    run_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    try:
        pred = model.predict(payload.image_reference)
        row = {
            "image_reference": payload.image_reference,
            "run_type": "single",
            "run_id": run_id,
            "batch_id": None,
            "predicted_gender": pred.predicted_gender,
            "predicted_sleeve": pred.predicted_sleeve,
            "gender_confidence": pred.gender_confidence,
            "sleeve_confidence": pred.sleeve_confidence,
            "model_name": model.model_name,
            "model_version": model.model_version,
            "status": "success",
            "error_message": None,
            "created_at": now,
        }
        log_prediction(row)
        return {"run_id": run_id, **row}
    except Exception as exc:
        row = {
            "image_reference": payload.image_reference,
            "run_type": "single",
            "run_id": run_id,
            "batch_id": None,
            "predicted_gender": None,
            "predicted_sleeve": None,
            "gender_confidence": None,
            "sleeve_confidence": None,
            "model_name": model.model_name,
            "model_version": model.model_version,
            "status": "error",
            "error_message": str(exc),
            "created_at": now,
        }
        log_prediction(row)
        return {"run_id": run_id, **row}


@app.post("/predict-batch")
def predict_batch(payload: PredictBatchRequest) -> dict[str, Any]:
    model = get_predictor()
    run_id = str(uuid4())
    batch_id = payload.batch_id or str(uuid4())
    results: list[dict[str, Any]] = []
    success_count = 0
    error_count = 0

    for image_reference in payload.image_references:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            pred = model.predict(image_reference)
            row = {
                "image_reference": image_reference,
                "run_type": "batch",
                "run_id": run_id,
                "batch_id": batch_id,
                "predicted_gender": pred.predicted_gender,
                "predicted_sleeve": pred.predicted_sleeve,
                "gender_confidence": pred.gender_confidence,
                "sleeve_confidence": pred.sleeve_confidence,
                "model_name": model.model_name,
                "model_version": model.model_version,
                "status": "success",
                "error_message": None,
                "created_at": now,
            }
            success_count += 1
        except Exception as exc:
            row = {
                "image_reference": image_reference,
                "run_type": "batch",
                "run_id": run_id,
                "batch_id": batch_id,
                "predicted_gender": None,
                "predicted_sleeve": None,
                "gender_confidence": None,
                "sleeve_confidence": None,
                "model_name": model.model_name,
                "model_version": model.model_version,
                "status": "error",
                "error_message": str(exc),
                "created_at": now,
            }
            error_count += 1

        log_prediction(row)
        results.append(row)

    return {
        "run_id": run_id,
        "batch_id": batch_id,
        "total_items": len(payload.image_references),
        "success_count": success_count,
        "error_count": error_count,
        "results": results,
    }


@app.get("/history")
def history(limit: int = Query(100, ge=1, le=1000)) -> list[dict[str, Any]]:
    return list_predictions(PREDICTIONS_DB, limit=limit)
