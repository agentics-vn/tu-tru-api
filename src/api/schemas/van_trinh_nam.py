"""Pydantic models for GET /v1/luu-nien/luan-context (Vận trình năm)."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

VerdictSignal = Literal["thuan", "than_trong", "trung_tinh", "hao"]
MonthArchetype = Literal["nang_do", "gieo_hat", "thu_hoach", "phong_thu", "chuyen_dong"]
EmphasisSignal = Literal["up", "down", "neutral"]


class VanTrinhNamMeta(BaseModel):
    product_title_vi: str
    year: int
    engine_version: str
    computed_at: str
    disclaimers: list[str] = Field(default_factory=list)


class VanTrinhNamSubject(BaseModel):
    birth_date: str
    birth_time: int
    gender: int


class HookYearBlock(BaseModel):
    year: int
    year_can_chi: str
    year_hanh: str
    element_relation: str
    year_rating: str
    year_theme_signal: str
    fact_bullets_vi: list[str]


class DaiVanCurrent(BaseModel):
    display: str
    can_hanh: str
    age_range: str
    relation_to_dung_than_signal: str


class DaiVanTransition(BaseModel):
    transition_month: int = Field(..., ge=1, le=12)
    from_display: str
    to_display: str
    applies_from_month: int = Field(..., ge=1, le=12)
    disclaimer_fact_vi: Optional[str] = None


class DaiVanBlock(BaseModel):
    current: Optional[DaiVanCurrent] = None
    transition_in_year: Optional[DaiVanTransition] = None
    disclaimer_fact_vi: Optional[str] = None


class YouThisYearBlock(BaseModel):
    natal_facts_vi: list[str]
    nhat_chu_hanh: str
    dung_than: str
    ky_than: str
    dai_van: DaiVanBlock


class AspectYearItem(BaseModel):
    aspect_id: Literal["su_nghiep", "tai_loc", "tinh_cam", "suc_khoe"]
    label_vi: str
    verdict_signal: VerdictSignal
    driver_tags: list[str]
    fact_bullets_vi: list[str]
    timing_tags: list[str] = Field(default_factory=list)


class PartABlock(BaseModel):
    hook_year: HookYearBlock
    you_this_year: YouThisYearBlock
    four_aspects_year: list[AspectYearItem] = Field(..., min_length=4, max_length=4)
    year_aspect_ranking: list[str]


class B1MonthTheme(BaseModel):
    luu_nguyet_display: str
    nap_am: str
    month_hanh: str
    element_relation_nhat_chu: str
    month_archetype: MonthArchetype
    fact_bullets_vi: list[str]


class B2EmphasisItem(BaseModel):
    aspect_id: str
    label_vi: str
    emphasis_signal: EmphasisSignal
    shift_tags: list[str]
    fact_bullets_vi: list[str]


class CalendarDayBest(BaseModel):
    date: str
    date_vi: str
    can_chi: str
    grade: str
    score: int


class CalendarDayAvoid(BaseModel):
    date: str
    date_vi: str
    can_chi: str
    grade: str
    score: int
    mitigation_tags: list[str]


class B3Calendar(BaseModel):
    best_days: list[CalendarDayBest] = Field(default_factory=list)
    avoid_days: list[CalendarDayAvoid] = Field(default_factory=list)
    top_hours: list[str] = Field(default_factory=list)
    calendar_stats: dict[str, Any] = Field(default_factory=dict)


class B4Action(BaseModel):
    action_tags_nen: list[str]
    action_tags_tranh: list[str] = Field(default_factory=list)
    fact_bullets_vi: list[str] = Field(default_factory=list)


class LuuNguyetMonth(BaseModel):
    month_num: int = Field(..., ge=1, le=12)
    target_month: str
    title_vi: str
    solar_range: str
    b1_month_theme: B1MonthTheme
    b2_month_emphasis: list[B2EmphasisItem] = Field(default_factory=list)
    b3_luu_nhat_calendar: B3Calendar
    b4_action: B4Action
    qa_hints: dict[str, Any]


class PartBBlock(BaseModel):
    luu_nguyet_months: list[LuuNguyetMonth] = Field(..., min_length=12, max_length=12)


class PartCBlock(BaseModel):
    closing_hints: Optional[dict[str, Any]] = None

    model_config = ConfigDict(extra="allow")


class PartDBlock(BaseModel):
    mechanics: dict[str, Any]


class VanTrinhNamLuanContextResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["success"] = "success"
    meta: VanTrinhNamMeta
    subject: VanTrinhNamSubject
    part_a: PartABlock
    part_b: PartBBlock
    part_c: dict[str, Any]
    part_d: PartDBlock
    score_methodology: dict[str, Any]
    writing_brief: dict[str, Any]


def validate_van_trinh_nam_luan_context(payload: dict) -> VanTrinhNamLuanContextResponse:
    return VanTrinhNamLuanContextResponse.model_validate(payload)
