"""Fixed packet notices (Section 12.2).

These are versioned templates. Semantic validation asserts that all four are present,
verbatim, in every packet. The Arabic renderings are for display only; the English text is
the canonical verbatim value that validation checks.
"""

from __future__ import annotations

from typing import Final, NamedTuple

NOTICE_TEMPLATE_VERSION: Final[str] = "packet-notices-v1.0.0"


class Notice(NamedTuple):
    notice_id: str
    heading_en: str
    text_en: str
    heading_ar: str
    text_ar: str


DECISION_SUPPORT_ONLY = Notice(
    notice_id="NOTICE_DECISION_SUPPORT_ONLY",
    heading_en="Decision-support only",
    text_en=(
        "NABD AI has prepared a cited Decision Readiness Packet. It has not approved, "
        "executed, transmitted, or activated any institutional action."
    ),
    heading_ar="لدعم القرار فقط",
    text_ar=(
        "أعدّ نبض الذكاء الاصطناعي حزمة جاهزية قرار موثّقة بالمصادر. ولم يوافق على أي إجراء "
        "مؤسسي أو ينفّذه أو يرسله أو يفعّله."
    ),
)

HUMAN_AUTHORITY = Notice(
    notice_id="NOTICE_HUMAN_AUTHORITY",
    heading_en="Human authority",
    text_en=(
        "An authorized human retains final authority and must act separately under the "
        "applicable institutional procedure."
    ),
    heading_ar="السلطة البشرية",
    text_ar=(
        "يحتفظ الشخص المخوّل بالسلطة النهائية، وعليه التصرف بشكل منفصل وفق الإجراء المؤسسي "
        "المعمول به."
    ),
)

EVIDENCE_LIMITATION = Notice(
    notice_id="NOTICE_EVIDENCE_LIMITATION",
    heading_en="Evidence limitation",
    text_en=(
        "Retrieved sources and model outputs are treated as untrusted data. Claims are "
        "limited to the admitted synthetic evidence recorded in this packet."
    ),
    heading_ar="حدود الأدلة",
    text_ar=(
        "تُعامل المصادر المسترجعة ومخرجات النموذج كبيانات غير موثوقة. وتقتصر الادعاءات على "
        "الأدلة الاصطناعية المقبولة والمسجّلة في هذه الحزمة."
    ),
)

PROTOTYPE_SCOPE = Notice(
    notice_id="NOTICE_PROTOTYPE_SCOPE",
    heading_en="Prototype scope",
    text_en=(
        "This packet was generated in ISOLATED_PROTOTYPE_V1 using synthetic data only. It "
        "does not demonstrate production, operational, or institutional authorization."
    ),
    heading_ar="نطاق النموذج الأولي",
    text_ar=(
        "أُنشئت هذه الحزمة في بيئة ISOLATED_PROTOTYPE_V1 باستخدام بيانات اصطناعية فقط. وهي "
        "لا تُثبت أي تفويض إنتاجي أو تشغيلي أو مؤسسي."
    ),
)

REQUIRED_NOTICES: Final[tuple[Notice, ...]] = (
    DECISION_SUPPORT_ONLY,
    HUMAN_AUTHORITY,
    EVIDENCE_LIMITATION,
    PROTOTYPE_SCOPE,
)

REQUIRED_NOTICE_IDS: Final[frozenset[str]] = frozenset(n.notice_id for n in REQUIRED_NOTICES)
NOTICE_TEXT_BY_ID: Final[dict[str, str]] = {n.notice_id: n.text_en for n in REQUIRED_NOTICES}


def notices_payload() -> list[dict[str, str]]:
    return [
        {
            "notice_id": notice.notice_id,
            "template_version": NOTICE_TEMPLATE_VERSION,
            "heading_en": notice.heading_en,
            "text_en": notice.text_en,
            "heading_ar": notice.heading_ar,
            "text_ar": notice.text_ar,
        }
        for notice in REQUIRED_NOTICES
    ]
