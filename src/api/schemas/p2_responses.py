"""OpenAPI response models for P2 endpoints (ngay-hom-nay, lich-thang, la-so, tu-tru, phong-thuy)."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from api.schemas.direction_c import (
    API_ERROR_RESPONSES,
    GioSlot,
    ScoreMethodology,
    ScoreMethodologyWeight,
)

# Re-export for route decorators
__all__ = ["API_ERROR_RESPONSES"]


# ── GET /v1/lich-thang ───────────────────────────────────────────────────────

class LichThangDaySummary(BaseModel):
    tot: list[str] = Field(default_factory=list)
    xau: list[str] = Field(default_factory=list)
    rating: str


class Sao28Brief(BaseModel):
    name: str
    hanh: str
    tot_xau: str


class LichThangDayItem(BaseModel):
    date: str
    lunar_day: int
    lunar_month: int
    lunar_label: str
    can_chi_name: str
    score: int
    grade: str
    day_type: str
    is_hoang_dao: bool
    star_name: str
    truc_name: str
    truc_score: int
    is_layer1_pass: bool
    badge: Literal["hoang_dao", "hac_dao"]
    gio_tot: list[GioSlot] = Field(default_factory=list)
    sao_28: Sao28Brief
    summary: LichThangDaySummary


class UserMenhBrief(BaseModel):
    hanh: str
    name: str


class LichThangResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: Literal["success"] = "success"
    month: str
    score_max: int = 100
    score_methodology: ScoreMethodology
    user_menh: UserMenhBrief
    days: list[LichThangDayItem] = Field(
        ...,
        description="Một phần tử cho mỗi ngày dương lịch trong tháng (28–31 ngày).",
    )


# ── GET /v1/ngay-hom-nay ─────────────────────────────────────────────────────

class CanChiBlock(BaseModel):
    name: str
    can_name: str
    chi_name: str
    nap_am_hanh: str


class LunarBlock(BaseModel):
    day: int
    month: int
    year: int
    display: str


class HoangDaoBlock(BaseModel):
    is_hoang_dao: bool
    star_name: str
    badge: str


class TrucBlock(BaseModel):
    name: str
    score: int


class DailyAdvice(BaseModel):
    nen_lam: str
    nen_tranh: str


class BatTuSection(BaseModel):
    model_config = ConfigDict(extra="allow")

    tu_tru_display: str
    nhat_chu: dict[str, str]
    dung_than: Optional[str] = None
    chart_strength: Optional[str] = None
    day_thap_than: Optional[str] = None
    dai_van: Optional[dict[str, str]] = None


class NgayHomNayResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: Literal["success"] = "success"
    date: str
    intent: str
    score: int
    grade: str
    score_max: int = 100
    score_methodology: ScoreMethodology
    can_chi: CanChiBlock
    lunar: LunarBlock
    hoang_dao: HoangDaoBlock
    truc: TrucBlock
    good_for: list[str] = Field(default_factory=list)
    avoid_for: list[str] = Field(default_factory=list)
    gio_tot: list[GioSlot] = Field(default_factory=list)
    gio_xau: list[GioSlot] = Field(default_factory=list)
    daily_advice: DailyAdvice
    bat_tu: Optional[BatTuSection] = None


# ── Shared chart contract (la-so / tu-tru) ────────────────────────────────────

class CanChiIdx(BaseModel):
    name: str
    idx: int


class NapAmPillar(BaseModel):
    name: str
    hanh: str
    mo_ta: Optional[str] = None


class PillarContract(BaseModel):
    can: CanChiIdx
    chi: CanChiIdx
    nap_am: NapAmPillar


class PillarsContract(BaseModel):
    year: PillarContract
    month: PillarContract
    day: PillarContract
    hour: PillarContract


class NhatChuBrief(BaseModel):
    can_name: str
    hanh: str


class ThapThanDominant(BaseModel):
    key: str
    name: str


class ThapThanContract(BaseModel):
    model_config = ConfigDict(extra="allow")

    dominant: ThapThanDominant
    year: Optional[str] = None
    month: Optional[str] = None
    hour: Optional[str] = None


class DaiVanCycle(BaseModel):
    model_config = ConfigDict(extra="allow")

    cycle_num: int
    display: str
    hanh: str
    age_range: str


class ChartContractP2(BaseModel):
    """Shared P2 chart block from build_la_so_chart_contract."""

    model_config = ConfigDict(extra="allow")

    pillars: PillarsContract
    nhat_chu: NhatChuBrief
    menh: dict[str, str]
    dung_than: str
    ky_than: str
    hi_than: Optional[str] = None
    cuu_than: Optional[str] = None
    cuong_nhuoc: Optional[str] = None
    chart_strength: Optional[str] = None
    thap_than: ThapThanContract
    element_counts: Optional[dict[str, float]] = None
    ngu_hanh: Optional[dict[str, float]] = None
    _raw: Optional[dict[str, Any]] = None
    dai_van: Optional[dict[str, Any]] = None
    dai_van_list: Optional[list[DaiVanCycle]] = None


class LaSoResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: Literal["success"] = "success"
    birth_date: str
    birth_time: int
    engine_version: str
    computed_at: str
    gender: Optional[int] = None
    pillars: PillarsContract
    nhat_chu: NhatChuBrief
    menh: dict[str, str]
    dung_than: str
    ky_than: str
    hi_than: Optional[str] = None
    cuu_than: Optional[str] = None
    cuong_nhuoc: Optional[str] = None
    chart_strength: Optional[str] = None
    thap_than: ThapThanContract
    element_counts: Optional[dict[str, float]] = None
    ngu_hanh: Optional[dict[str, float]] = None
    _raw: Optional[dict[str, Any]] = None
    dai_van: Optional[dict[str, Any]] = None
    dai_van_list: Optional[list[DaiVanCycle]] = None
    tinh_cach: Optional[dict[str, Any]] = None
    su_nghiep: Optional[dict[str, Any]] = None
    tai_van: Optional[dict[str, Any]] = None
    suc_khoe: Optional[dict[str, Any]] = None
    tinh_duyen: Optional[dict[str, Any]] = None
    dai_van_current: Optional[dict[str, Any]] = None


class TuTruMenhBasic(BaseModel):
    nap_am_name: str
    hanh: str
    duong_than: str
    ky_than: str


class TuTruResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: Literal["success"] = "success"
    birth_date: str
    engine_version: str
    computed_at: str
    birth_year_can_chi: str
    menh: TuTruMenhBasic
    birth_time: Optional[int] = None
    birth_time_label: Optional[str] = None
    tu_tru_display: Optional[str] = None
    gender: Optional[int] = None
    pillars: Optional[dict[str, Any]] = None
    nhat_chu: Optional[NhatChuBrief] = None
    chart_strength: Optional[str] = None
    element_counts: Optional[dict[str, float]] = None
    support_ratio: Optional[float] = None
    dung_than: Optional[dict[str, Any]] = None
    hi_than: Optional[dict[str, Any]] = None
    ky_than: Optional[dict[str, Any]] = None
    cuu_than: Optional[dict[str, Any]] = None
    thap_than: Optional[dict[str, Any]] = None
    dai_van: Optional[dict[str, Any]] = None
    dai_van_list: Optional[list[DaiVanCycle]] = None
    cuong_nhuoc: Optional[str] = None
    ngu_hanh: Optional[dict[str, float]] = None
    _raw: Optional[dict[str, Any]] = None


# ── GET /v1/phong-thuy v2 ─────────────────────────────────────────────────────

class HuongItem(BaseModel):
    direction: str
    element: str
    reason: str


class MauItem(BaseModel):
    color: str
    hex: str
    element: str


class PhiTinhDirection(BaseModel):
    direction: str
    star: int
    star_name: str
    hanh: str
    nature: str
    meaning: str


class PhiTinhRemedy(BaseModel):
    direction: str
    star: int
    remedy: str


class PhongThuyResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: Literal["success"] = "success"
    version: Literal[2] = 2
    purpose: str
    user_menh: UserMenhBrief
    dung_than: str
    ky_than: str
    huong_tot: list[HuongItem] = Field(default_factory=list)
    huong_xau: list[HuongItem] = Field(default_factory=list)
    mau_may_man: list[MauItem] = Field(default_factory=list)
    mau_ky: list[MauItem] = Field(default_factory=list)
    so_may_man: list[int] = Field(default_factory=list)
    so_ky: list[int] = Field(default_factory=list)
    vat_pham: list[dict[str, Any]] = Field(default_factory=list)
    purpose_specific: Optional[dict[str, Any]] = None
    personalization: Optional[dict[str, Any]] = None
    couple_harmony: Optional[dict[str, Any]] = None
    phi_tinh_year: Optional[int] = None
    phi_tinh: Optional[list[PhiTinhDirection]] = None
    huong_tot_nam_nay: Optional[list[str]] = None
    huong_xau_nam_nay: Optional[list[str]] = None
    hoa_giai: Optional[list[PhiTinhRemedy]] = None
    phi_tinh_note_vi: Optional[str] = None
