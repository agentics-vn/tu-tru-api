"""Pydantic models for Direction C API contract."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class BreakdownItem(BaseModel):
    id: str
    source: str
    source_ref: int
    type: str
    points: int
    reason_vi: str


class ScoreMethodologyWeight(BaseModel):
    factor: str
    label_vi: str
    max_points: int


class ScoreMethodology(BaseModel):
    summary_vi: str
    weights: list[ScoreMethodologyWeight]


class RankedDay(BaseModel):
    rank: int
    date: str
    score: int
    grade: str
    can_chi_day: str
    lunar_label: str
    truc: str
    gio_tot: list[dict[str, Any]] = Field(default_factory=list)
    reason_vi: str


class EmptyChonNgayResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: str = "success"
    intent: str
    intent_label_vi: str
    range_start: str
    range_end: str
    ranked_days: list[RankedDay] = Field(default_factory=list)
    empty_reason_vi: Optional[str] = None
    score_max: int = 100
    score_methodology: ScoreMethodology


def validate_chon_ngay_response(payload: dict) -> EmptyChonNgayResponse:
    """Validate Direction C chon-ngay top-level contract (ignores legacy/extra keys)."""
    return EmptyChonNgayResponse.model_validate(payload)


class DayDetailPersonalizedResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: str = "success"
    date: str
    score: int
    grade: str
    breakdown: list[BreakdownItem]
    personalized: bool = True
    purpose_rows: list[dict[str, Any]] = Field(default_factory=list)


class DayDetailGenericResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: str = "success"
    date: str
    score: int
    grade: str
    breakdown_generic: list[BreakdownItem]
    personalized: bool = False


class DayCompareResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: str = "success"
    date_a: str
    date_b: str
    score_a: int
    score_b: int
    delta_score: int
    comparison_vi: str
    better_for: list[str] | str
    sources: list[dict[str, Any]] | list[str]


class LuanContextResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: str = "success"
    date_iso: str
    score: int
    grade: str
    breakdown_summary: list[dict[str, Any]]
    gio_tot: list[dict[str, Any]] = Field(default_factory=list)
    gio_xau: list[dict[str, Any]] = Field(default_factory=list)


def validate_day_detail_response(payload: dict, *, personalized: bool) -> None:
    if personalized:
        DayDetailPersonalizedResponse.model_validate(payload)
    else:
        DayDetailGenericResponse.model_validate(payload)


def validate_day_compare_response(payload: dict) -> DayCompareResponse:
    return DayCompareResponse.model_validate(payload)


def validate_luan_context_response(payload: dict) -> LuanContextResponse:
    return LuanContextResponse.model_validate(payload)
