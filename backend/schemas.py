from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PredictSingleRequest(BaseModel):
    image_reference: str = Field(..., description="Relative path, absolute path, or image URL.")


class PredictBatchRequest(BaseModel):
    image_references: list[str] = Field(..., min_length=1, max_length=200)
    batch_id: str | None = None


class PredictionResult(BaseModel):
    image_reference: str
    predicted_gender: str | None
    predicted_sleeve: str | None
    gender_confidence: float | None
    sleeve_confidence: float | None
    model_name: str
    model_version: str
    status: Literal["success", "error"]
    error_message: str | None = None


class PredictionLogRow(BaseModel):
    id: int
    image_reference: str
    run_type: str
    run_id: str
    batch_id: str | None
    predicted_gender: str | None
    predicted_sleeve: str | None
    gender_confidence: float | None
    sleeve_confidence: float | None
    model_name: str
    model_version: str
    status: str
    error_message: str | None
    created_at: datetime
