"""
la_so.py — Lá số diễn giải: structured reading (nhãn ngữ nghĩa) từ Tứ Trụ đã tính.

Không gọi LLM. Dùng các hàm engine có sẵn + bảng map cứng cho App / Supabase EF.
"""

from __future__ import annotations

from typing import Any, Optional

from engine.cuong_nhuoc import analyze_chart_strength
from engine.dai_van import get_current_dai_van
from engine.dung_than import find_dung_than
from engine.thap_than import analyze_thap_than

# ── Nhật Chủ (Thiên Can Nhật) → archetype ───────────────────────────────────

NHAT_CHU_ARCHETYPE: dict[int, dict[str, Any]] = {
    0: {
        "archetype": "Đại thụ",
        "image": "Cây cổ thụ — vững vàng, che chở, hướng lên",
        "core_traits": ["Lãnh đạo tự nhiên", "Chính trực", "Bảo thủ, khó thay đổi"],
        "element": "Mộc",
        "polarity": "Dương",
    },
    1: {
        "archetype": "Dây leo",
        "image": "Hoa cỏ, dây leo — mềm mại nhưng bền bỉ, thích ứng",
        "core_traits": ["Linh hoạt", "Khéo léo ngoại giao", "Kiên trì ẩn giấu"],
        "element": "Mộc",
        "polarity": "Âm",
    },
    2: {
        "archetype": "Mặt trời",
        "image": "Mặt trời — rực rỡ, soi sáng, phóng khoáng",
        "core_traits": ["Nhiệt huyết", "Lạc quan", "Thiếu kiên nhẫn chi tiết"],
        "element": "Hỏa",
        "polarity": "Dương",
    },
    3: {
        "archetype": "Ngọn nến",
        "image": "Ngọn nến, ánh đuốc — ấm áp, tinh tế, soi rõ trong bóng tối",
        "core_traits": ["Tinh tế", "Trực giác mạnh", "Dễ cháy hết mình"],
        "element": "Hỏa",
        "polarity": "Âm",
    },
    4: {
        "archetype": "Núi lớn",
        "image": "Núi — vững chãi, đáng tin cậy, ít thay đổi",
        "core_traits": ["Đáng tin cậy", "Bao dung", "Chậm thích nghi"],
        "element": "Thổ",
        "polarity": "Dương",
    },
    5: {
        "archetype": "Ruộng đồng",
        "image": "Đất vườn — nuôi dưỡng, chăm sóc, khiêm nhường",
        "core_traits": ["Chu đáo", "Thực tế", "Hay lo lắng"],
        "element": "Thổ",
        "polarity": "Âm",
    },
    6: {
        "archetype": "Kiếm thép",
        "image": "Kiếm, rìu — sắc bén, quyết đoán, cứng rắn",
        "core_traits": ["Quyết đoán", "Trọng nghĩa khí", "Dễ gây xung đột"],
        "element": "Kim",
        "polarity": "Dương",
    },
    7: {
        "archetype": "Trang sức",
        "image": "Vàng bạc, trang sức — tinh xảo, thẩm mỹ, nhạy cảm",
        "core_traits": ["Thẩm mỹ cao", "Cầu toàn", "Dễ tổn thương"],
        "element": "Kim",
        "polarity": "Âm",
    },
    8: {
        "archetype": "Đại dương",
        "image": "Biển cả, sông lớn — bao la, tự do, khó kiểm soát",
        "core_traits": ["Tư duy rộng", "Thích tự do", "Khó tập trung một việc"],
        "element": "Thủy",
        "polarity": "Dương",
    },
    9: {
        "archetype": "Mưa sương",
        "image": "Mưa phùn, sương mai — nhẹ nhàng, thấm sâu, nuôi dưỡng âm thầm",
        "core_traits": ["Nhạy cảm", "Quan sát tốt", "Hay suy nghĩ nhiều"],
        "element": "Thủy",
        "polarity": "Âm",
    },
}

STRENGTH_NOTES: dict[str, str] = {
    "vượng": "Cá tính mạnh, tự chủ, nhưng dễ cứng đầu.",
    "nhược": "Cần sự hỗ trợ, nên tìm đối tác mạnh để bổ trợ.",
    "cân bằng": "Tính cách ôn hòa, dễ thích nghi.",
}

# ── Thập Thần chủ đạo → sự nghiệp / tài ─────────────────────────────────────

THAP_THAN_CAREER: dict[str, dict[str, Any]] = {
    "chinh_tai": {
        "career_tendency": "Quản lý tài chính, kinh doanh ổn định",
        "suitable_fields": ["Tài chính, kế toán", "Kinh doanh bán lẻ", "Bất động sản"],
        "wealth_style": "Thu nhập ổn định từ công sức. Tiền đến đều đặn.",
        "wealth_risk": "Ít khi có 'trúng mánh'. Nên tích lũy, không nên đầu cơ.",
    },
    "thien_tai": {
        "career_tendency": "Đầu tư, kinh doanh mạo hiểm, nhiều nguồn thu",
        "suitable_fields": ["Đầu tư tài chính", "Kinh doanh đa ngành", "Bất động sản đầu cơ"],
        "wealth_style": "Tiền đến bất ngờ, từ nhiều nguồn. Có khả năng kiếm tiền lớn.",
        "wealth_risk": "Dễ mất tiền nhanh như kiếm được. Cần kỷ luật tài chính.",
    },
    "chinh_quan": {
        "career_tendency": "Công chức, quản lý, tổ chức lớn",
        "suitable_fields": ["Nhà nước, hành chính", "Luật sư, pháp lý", "Quản lý cấp cao"],
        "wealth_style": "Thu nhập từ lương, thăng tiến. Ổn định nhưng có trần.",
        "wealth_risk": "Không nên kinh doanh riêng. Phát triển trong tổ chức là tốt nhất.",
    },
    "that_sat": {
        "career_tendency": "Cạnh tranh cao, quân đội, thể thao, khởi nghiệp",
        "suitable_fields": ["Quân đội, công an", "Kinh doanh cạnh tranh", "Thể thao, võ thuật"],
        "wealth_style": "Kiếm tiền bằng sức mạnh và quyết đoán.",
        "wealth_risk": "Áp lực cao. Thành công lớn hoặc thất bại lớn, ít trung dung.",
    },
    "chinh_an": {
        "career_tendency": "Giáo dục, nghiên cứu, tôn giáo, nghệ thuật",
        "suitable_fields": ["Giáo viên, giảng viên", "Nghiên cứu, học thuật", "Tôn giáo, tâm linh"],
        "wealth_style": "Không thiên về tiền bạc. Giàu tri thức hơn vật chất.",
        "wealth_risk": "Dễ bỏ lỡ cơ hội kinh doanh vì ưu tiên tri thức.",
    },
    "thien_an": {
        "career_tendency": "Sáng tạo, nghệ thuật phi truyền thống, tâm linh",
        "suitable_fields": ["Nghệ thuật, sáng tạo", "Phong thủy, tâm linh", "Công nghệ mới"],
        "wealth_style": "Thu nhập từ tài năng đặc biệt. Không theo khuôn mẫu.",
        "wealth_risk": "Thu nhập không ổn định. Cần có kế hoạch tài chính dài hạn.",
    },
    "thuc_than": {
        "career_tendency": "Ẩm thực, giải trí, giáo dục, tự do",
        "suitable_fields": ["Nhà hàng, ẩm thực", "Giải trí, truyền thông", "Tự do nghề nghiệp"],
        "wealth_style": "Kiếm tiền từ sở thích. Biến đam mê thành thu nhập.",
        "wealth_risk": "Dễ hưởng thụ quá mức. Cần cân bằng giữa chi tiêu và tích lũy.",
    },
    "thuong_quan": {
        "career_tendency": "Sáng tạo đột phá, nghệ sĩ, freelancer, phản biện",
        "suitable_fields": ["Nghệ thuật, thiết kế", "Luật sư tranh tụng", "Startup, đổi mới"],
        "wealth_style": "Kiếm tiền bằng tài năng độc đáo. Không thích làm thuê.",
        "wealth_risk": "Xung đột với cấp trên. Nên tự kinh doanh hoặc làm freelance.",
    },
    "ty_kien": {
        "career_tendency": "Cạnh tranh ngang hàng, kinh doanh độc lập",
        "suitable_fields": ["Kinh doanh cá nhân", "Thể thao, cạnh tranh", "Bán hàng"],
        "wealth_style": "Tự lực cánh sinh. Kiếm tiền bằng nỗ lực bản thân.",
        "wealth_risk": "Cạnh tranh nhiều. Khó hợp tác, dễ bị tranh giành.",
    },
    "kiep_tai": {
        "career_tendency": "Kinh doanh rủi ro, đầu cơ, cờ bạc",
        "suitable_fields": ["Bán hàng áp lực cao", "Chứng khoán, đầu cơ", "Kinh doanh mạo hiểm"],
        "wealth_style": "Tiền đến nhanh đi nhanh. Dễ bị người khác tranh mất.",
        "wealth_risk": "Rủi ro cao. Cần giữ tiền cẩn thận, tránh cho vay, bảo lãnh.",
    },
}

_DEFAULT_CAREER: dict[str, Any] = {
    "career_tendency": "Đa dạng theo bối cảnh — cần xem thêm Thập Thần chi tiết",
    "suitable_fields": [],
    "wealth_style": "Cân nhắc theo lá số tổng thể.",
    "wealth_risk": "Theo dõi cân bằng ngũ hành và Dụng Thần.",
}

HANH_HEALTH: dict[str, dict[str, str]] = {
    "Kim": {
        "organ": "Phổi, đại tràng, da",
        "risk_when_weak": "Hô hấp, dị ứng, da liễu",
        "risk_when_strong": "Viêm phổi, táo bón",
    },
    "Mộc": {
        "organ": "Gan, mật, gân cơ",
        "risk_when_weak": "Mệt mỏi, suy gan",
        "risk_when_strong": "Nóng gan, đau đầu, mất ngủ",
    },
    "Thủy": {
        "organ": "Thận, bàng quang, xương",
        "risk_when_weak": "Thận yếu, đau lưng, yếu xương",
        "risk_when_strong": "Phù nề, tiểu đường",
    },
    "Hỏa": {
        "organ": "Tim, ruột non, huyết áp",
        "risk_when_weak": "Huyết áp thấp, thiếu máu",
        "risk_when_strong": "Huyết áp cao, nóng trong",
    },
    "Thổ": {
        "organ": "Dạ dày, lá lách, tiêu hóa",
        "risk_when_weak": "Tiêu hóa kém, suy nhược",
        "risk_when_strong": "Thừa cân, tiểu đường",
    },
}


def _build_tinh_duyen(
    gender: int,
    thap_than: dict[str, Any],
    dm_strength: str,
) -> dict[str, Any]:
    gods = thap_than["god_counts"]

    if gender == 1:
        spouse_key = "chinh_tai"
        affair_key = "thien_tai"
        spouse_label = "Chính Tài (vợ)"
    else:
        spouse_key = "chinh_quan"
        affair_key = "that_sat"
        spouse_label = "Chính Quan (chồng)"

    spouse_count = gods.get(spouse_key, 0)
    affair_count = gods.get(affair_key, 0)

    return {
        "spouse_star": spouse_label,
        "spouse_presence": spouse_count,
        "affair_presence": affair_count,
        "dm_strength": dm_strength,
        "signals": {
            "strong_spouse": spouse_count >= 1,
            "multiple_affair": affair_count >= 2,
            "weak_dm_needs_support": dm_strength == "nhược",
            "strong_dm_dominant": dm_strength == "vượng",
        },
    }


def build_la_so(
    tu_tru: dict,
    gender: Optional[int],
    birth_date_iso: str,
) -> dict[str, Any]:
    """
    Gom structured reading từ Tứ Trụ (đã có đủ 4 trụ + Nhật Chủ).

    Args:
        tu_tru: từ get_tu_tru(iso_date, birth_time)
        gender: 1 nam | -1 nữ | None (bỏ qua tình duyên & đại vận timeline)
        birth_date_iso: YYYY-MM-DD (cho get_dai_van / get_current_dai_van)
    """
    dm_can_idx = tu_tru["day"]["can_idx"]
    dm_hanh = tu_tru["nhat_chu"]["hanh"]

    strength_info = analyze_chart_strength(tu_tru)
    dung_than_info = find_dung_than(tu_tru)
    thap_than = analyze_thap_than(tu_tru)
    dominant_key = thap_than["dominant_god"]["key"]
    career = THAP_THAN_CAREER.get(dominant_key, _DEFAULT_CAREER)
    health = HANH_HEALTH.get(dm_hanh, {
        "organ": "",
        "risk_when_weak": "",
        "risk_when_strong": "",
    })
    archetype = NHAT_CHU_ARCHETYPE[dm_can_idx]
    strength = strength_info["strength"]

    result: dict[str, Any] = {
        "tinh_cach": {
            **archetype,
            "strength": strength,
            "strength_note": STRENGTH_NOTES.get(
                strength,
                STRENGTH_NOTES["cân bằng"],
            ),
        },
        "su_nghiep": {
            "dominant_thap_than": thap_than["dominant_god"]["name"],
            "dominant_thap_than_key": dominant_key,
            **career,
            "dung_than_element": dung_than_info["dung_than"],
            "element_tip": (
                f"Ngành nghề liên quan hành {dung_than_info['dung_than']} "
                f"sẽ thuận lợi hơn."
            ),
        },
        "tai_van": {
            "wealth_style": career["wealth_style"],
            "wealth_risk": career["wealth_risk"],
            "dung_than": dung_than_info["dung_than"],
            "hi_than": dung_than_info["hi_than"],
            "ky_than": dung_than_info["ky_than"],
        },
        "suc_khoe": {
            "dm_element": dm_hanh,
            "dm_strength": strength,
            **health,
            "health_context": (
                "risk_when_weak" if strength == "nhược" else "risk_when_strong"
            ),
            "boost_element": dung_than_info["dung_than"],
            "avoid_element": dung_than_info["ky_than"],
        },
    }

    if gender in (1, -1):
        result["tinh_duyen"] = _build_tinh_duyen(gender, thap_than, strength)

        current_dv = get_current_dai_van(tu_tru, gender, birth_date_iso)
        if current_dv:
            result["dai_van_current"] = {
                "display": current_dv["display"],
                "hanh": current_dv["can_hanh"],
                "nap_am_hanh": current_dv["nap_am_hanh"],
                "age_range": f"{current_dv['start_age']}-{current_dv['end_age']}",
            }

    result["_raw"] = {
        "tu_tru_display": tu_tru["display"],
        "element_counts": strength_info["element_counts"],
        "support_ratio": strength_info["support_ratio"],
        "thap_than_profile": {
            "year": thap_than["year_god"]["name"],
            "month": thap_than["month_god"]["name"],
            "hour": thap_than["hour_god"]["name"],
        },
        "god_counts": thap_than["god_counts"],
    }

    return result
