"""Pydantic models for Direction C API contract and OpenAPI documentation."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# ── Shared ────────────────────────────────────────────────────────────────────

class ApiErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    error_code: str
    message: str
    message_en: str


class GioSlot(BaseModel):
    chi: str
    chi_name: str
    start_hour: str
    end_hour: str
    label_vi: str
    range: str


class SourceRef(BaseModel):
    ref: int
    label_vi: str
    description_vi: str


class ScoreMethodologyWeight(BaseModel):
    factor: str
    label_vi: str
    max_points: int


class ScoreMethodology(BaseModel):
    summary_vi: str
    weights: list[ScoreMethodologyWeight]


class BreakdownItem(BaseModel):
    id: str
    source: str
    source_ref: int
    type: str
    points: int
    reason_vi: str


class BreakdownSummaryItem(BaseModel):
    id: str
    label_vi: str
    verdict_vi: str
    reason_vi: str
    points: int
    source_ref: int


class PurposeRow(BaseModel):
    intent: str
    intent_label_vi: str
    short_label_vi: str
    verdict: Literal["tot", "xau", "luu_y", "trung"]
    reason_vi: str


class RenderCard(BaseModel):
    model_config = ConfigDict(extra="allow")

    headline: str
    lunar_line: str
    badge: str
    score_pct: int
    intent_vi: str
    element: str
    truc: str
    stars: list[str] = Field(default_factory=list)
    one_liner: Optional[str] = None
    best_hours: list[str] = Field(default_factory=list)


class DateToAvoid(BaseModel):
    date: str
    reason_vi: str
    severity: int
    summary_vi: Optional[str] = None


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    version: str
    engine_version: str


# ── POST /v1/chon-ngay ──────────────────────────────────────────────────────

class RankedDay(BaseModel):
    rank: int
    date: str
    lunar_date: str
    lunar_label: str
    score: int
    grade: str
    can_chi_day: str
    truc: str
    gio_tot: list[GioSlot] = Field(default_factory=list)
    reason_vi: str
    summary_vi: Optional[str] = None
    sao_cat: list[str] = Field(default_factory=list)
    sao_hung: list[str] = Field(default_factory=list)
    nguhanh_day: Optional[str] = None
    time_slots: list[GioSlot] = Field(default_factory=list)
    render_card: Optional[RenderCard] = None


class ChonNgayMeta(BaseModel):
    model_config = ConfigDict(extra="allow")

    intent: str
    range_scanned: dict[str, str]
    total_days_scanned: int
    days_passed_layer1: int
    days_passed_layer2: int
    candidates_scanned: int
    bat_tu_summary: dict[str, Any]
    share_token: Optional[str] = None


class ChonNgayResponse(BaseModel):
    """Direction C chon-ngay response (OpenAPI + runtime validation)."""

    model_config = ConfigDict(extra="ignore")

    status: Literal["success"] = "success"
    intent: str
    intent_label_vi: str
    range_start: str
    range_end: str
    score_max: int = 100
    score_methodology: ScoreMethodology
    empty_reason_vi: Optional[str] = None
    meta: ChonNgayMeta
    ranked_days: list[RankedDay] = Field(default_factory=list)
    recommended_dates: list[RankedDay] = Field(default_factory=list)
    dates_to_avoid: list[DateToAvoid] = Field(default_factory=list)
    sources: list[SourceRef] = Field(default_factory=list)


class ShareChonNgayResponse(ChonNgayResponse):
    shared: bool = True
    endpoint: str = "chon-ngay"


def validate_chon_ngay_response(payload: dict) -> ChonNgayResponse:
    return ChonNgayResponse.model_validate(payload)


# ── GET /v1/day-detail ──────────────────────────────────────────────────────

class DayDetailResponse(BaseModel):
    """Unified day-detail schema (generic + personalized fields)."""

    model_config = ConfigDict(extra="ignore")

    status: Literal["success"] = "success"
    date: str
    lunar_date: str
    lunar_label: str
    can_chi: str
    can_chi_day: str
    hoang_dao: bool
    star_name: str
    truc_name: str
    truc_score: int
    sao_28: str
    sao_element: str
    gio_tot: list[GioSlot] = Field(default_factory=list)
    gio_xau: list[GioSlot] = Field(default_factory=list)
    hung_ngay: list[str] = Field(default_factory=list)
    score: int
    grade: str
    score_max: int = 100
    score_methodology: ScoreMethodology
    sources: list[SourceRef] = Field(default_factory=list)
    personalized: bool
    breakdown: Optional[list[BreakdownItem]] = None
    breakdown_generic: Optional[list[BreakdownItem]] = None
    summary_vi: Optional[str] = None
    intent: Optional[str] = None
    good_for: Optional[list[str]] = None
    avoid_for: Optional[list[str]] = None
    purpose_rows: Optional[list[PurposeRow]] = None


def validate_day_detail_response(payload: dict, *, personalized: bool) -> DayDetailResponse:
    return DayDetailResponse.model_validate(payload)


# ── GET /v1/day-detail/luan-context ─────────────────────────────────────────

class LuanContextResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: Literal["success"] = "success"
    date_iso: str
    can_chi_day: str
    score: int
    grade: str
    menh_user: str
    breakdown_summary: list[BreakdownSummaryItem]
    sources: list[SourceRef]
    gio_tot: list[GioSlot] = Field(default_factory=list)
    gio_xau: list[GioSlot] = Field(default_factory=list)
    gio_tot_labels: list[str] = Field(default_factory=list)
    gio_xau_labels: list[str] = Field(default_factory=list)
    scope_hint_vi: str
    anchor_question_hint_vi: str
    suggested_followups: list[str] = Field(default_factory=list)


def validate_luan_context_response(payload: dict) -> LuanContextResponse:
    return LuanContextResponse.model_validate(payload)


# ── GET /v1/day-compare ─────────────────────────────────────────────────────

class DayCompareResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: Literal["success"] = "success"
    date_a: str
    date_b: str
    score_a: int
    score_b: int
    delta_score: int
    comparison_vi: str
    better_for: list[str]
    sources: list[SourceRef]


def validate_day_compare_response(payload: dict) -> DayCompareResponse:
    return DayCompareResponse.model_validate(payload)


# ── POST /v1/chon-ngay/detail (partial — layers vary) ───────────────────────

class ChonNgayDetailResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: Literal["success"] = "success"
    date: str
    lunar_date: str
    can_chi_day: str
    nguhanh_day: Optional[str] = None
    verdict: Optional[str] = None
    verdict_vi: Optional[str] = None
    severity: Optional[int] = None
    layer1: Optional[dict[str, Any]] = None
    layer2: Optional[dict[str, Any]] = None
    layer3: Optional[dict[str, Any]] = None
    layer1_fail_reasons: Optional[list[str]] = None
    time_slots: Optional[list[GioSlot]] = None
    score: Optional[int] = None
    grade: Optional[str] = None
    breakdown: Optional[list[BreakdownItem]] = None
    score_max: Optional[int] = None
    score_methodology: Optional[ScoreMethodology] = None
    sources: Optional[list[SourceRef]] = None
    reason_vi: Optional[str] = None
    summary_vi: Optional[str] = None


# ── GET /v1/la-so/luu-nien ──────────────────────────────────────────────────

class LuuNienLifeArea(BaseModel):
    area: str
    outlook_vi: str


class LuuNienMonthScore(BaseModel):
    month: int
    score: int


class LuuNienResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: Literal["success"] = "success"
    birth_date: str
    engine_version: str
    computed_at: str
    year: int
    year_can_chi: str
    year_label_vi: str
    element_relation: str
    year_rating: str
    year_theme_vi: str
    life_areas: list[LuuNienLifeArea] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    month_scores: list[LuuNienMonthScore] = Field(default_factory=list)
    assumptions_vi: list[str] = Field(default_factory=list)


# Fix API_ERROR_RESPONSES to use classes not strings
API_ERROR_RESPONSES = {
    400: {"model": ApiErrorResponse, "description": "INVALID_INPUT hoặc RANGE_TOO_LARGE"},
    500: {"model": ApiErrorResponse, "description": "INTERNAL_ERROR"},
}

# Backward alias
EmptyChonNgayResponse = ChonNgayResponse
DayDetailPersonalizedResponse = DayDetailResponse
DayDetailGenericResponse = DayDetailResponse
