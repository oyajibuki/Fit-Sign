import re
import json as _json
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from db import get_user


def _register_fonts():
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))
        pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
        return "HeiseiKakuGo-W5", "HeiseiMin-W3"
    except Exception:
        return "Helvetica-Bold", "Helvetica"


def _parse_extra(raw_content: str):
    """Split ␞-encoded extra JSON out of the stored content field."""
    if "␞" in raw_content:
        content_part, extra_json = raw_content.split("␞", 1)
        try:
            extra = _json.loads(extra_json)
        except Exception:
            extra = {}
    else:
        content_part = raw_content
        extra = {}
    return content_part, extra


def generate_pdf(contract: dict) -> BytesIO:
    bold_font, normal_font = _register_fonts()

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=25 * mm,
        leftMargin=25 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    # ── Styles ─────────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "ContractTitle",
        fontName=bold_font,
        fontSize=18,
        leading=26,
        alignment=TA_CENTER,
        spaceAfter=2,
        textColor=colors.HexColor("#111827"),
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        fontName=normal_font,
        fontSize=9,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#6B7280"),
        spaceAfter=10,
    )
    article_header_style = ParagraphStyle(
        "ArticleHeader",
        fontName=bold_font,
        fontSize=11,
        leading=18,
        alignment=TA_LEFT,
        spaceBefore=10,
        spaceAfter=3,
        textColor=colors.HexColor("#111827"),
    )
    body_style = ParagraphStyle(
        "Body",
        fontName=normal_font,
        fontSize=10,
        leading=18,
        alignment=TA_LEFT,
        spaceAfter=3,
        leftIndent=4,
        textColor=colors.HexColor("#1F2937"),
    )
    intro_style = ParagraphStyle(
        "Intro",
        fontName=normal_font,
        fontSize=10,
        leading=18,
        alignment=TA_LEFT,
        spaceAfter=6,
        textColor=colors.HexColor("#374151"),
    )
    label_style = ParagraphStyle(
        "Label",
        fontName=bold_font,
        fontSize=9,
        leading=14,
        textColor=colors.HexColor("#6B7280"),
    )
    value_style = ParagraphStyle(
        "Value",
        fontName=normal_font,
        fontSize=10,
        leading=16,
        textColor=colors.HexColor("#111827"),
    )
    small_style = ParagraphStyle(
        "Small",
        fontName=normal_font,
        fontSize=8,
        leading=12,
        textColor=colors.HexColor("#9CA3AF"),
    )

    story = []

    # ── Resolve contract fields ─────────────────────────────────────────────
    raw_content = contract.get("content", "")
    content_part, extra = _parse_extra(raw_content)

    creator = get_user(contract.get("creator_id"))
    creator_name = creator.get("display_name") or "未登録" if creator else "未登録"
    signer_name = contract.get("signer_name") or "（受託者）"

    body_template = contract.get("template_body", "")
    try:
        body_text = body_template.format(
            content=content_part,
            amount=contract.get("amount", ""),
            contract_date=contract.get("contract_date", ""),
            creator_name=creator_name,
            signer_name=signer_name,
            start_date=extra.get("start_date", contract.get("contract_date", "")),
            end_date=extra.get("end_date", ""),
            payment_unit=extra.get("payment_unit", ""),
            deadline=extra.get("deadline", contract.get("contract_date", "")),
        )
    except KeyError:
        body_text = body_template

    lines = body_text.split("\n")

    # ── Determine title from first non-empty line ───────────────────────────
    # The first line of the template body IS the title.
    title_text = ""
    body_lines_start = 0
    for i, ln in enumerate(lines):
        if ln.strip():
            title_text = ln.strip()
            body_lines_start = i + 1
            break

    # ── Document header ─────────────────────────────────────────────────────
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(title_text, title_style))
    story.append(Paragraph(
        f"FitSign 合意記録　|　契約ID: {contract.get('id', '')}",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#17C080")))
    story.append(Spacer(1, 6 * mm))

    # ── Render body lines intelligently ────────────────────────────────────
    # Detect article headers: "第X条（...）" or "第X条(...)"
    article_re = re.compile(r"^第\d+条[（(]")
    # Detect numbered sub-items: "1. ..." or "2. ..."
    num_item_re = re.compile(r"^\d+\.")
    # Detect the signing line (【甲】/【乙】 pattern)
    sign_re = re.compile(r"^【[甲乙]】|^【.*【")

    remaining = lines[body_lines_start:]
    prev_was_blank = False

    for line in remaining:
        stripped = line.strip()

        if not stripped:
            if not prev_was_blank:
                story.append(Spacer(1, 3 * mm))
            prev_was_blank = True
            continue

        prev_was_blank = False

        if article_re.match(stripped):
            # Article header — bold, add space above
            story.append(Spacer(1, 4 * mm))
            story.append(Paragraph(stripped, article_header_style))

        elif sign_re.match(stripped):
            # Signature line — bold, indented
            story.append(Spacer(1, 6 * mm))
            story.append(Paragraph(stripped, ParagraphStyle(
                "SignLine",
                fontName=bold_font,
                fontSize=10,
                leading=18,
                spaceAfter=3,
                textColor=colors.HexColor("#111827"),
            )))

        elif stripped.startswith("対象業務") or stripped.startswith("業務内容"):
            # Highlighted key-value lines
            story.append(Paragraph(stripped, ParagraphStyle(
                "KeyValue",
                fontName=bold_font,
                fontSize=10,
                leading=18,
                leftIndent=8,
                spaceAfter=3,
                textColor=colors.HexColor("#065F46"),
            )))

        elif num_item_re.match(stripped):
            # Numbered sub-item
            story.append(Paragraph(stripped, ParagraphStyle(
                "SubItem",
                fontName=normal_font,
                fontSize=10,
                leading=18,
                leftIndent=12,
                spaceAfter=3,
                textColor=colors.HexColor("#1F2937"),
            )))

        elif i == 0 or (any(stripped.startswith(p) for p in ["私（", "委託者（", "発注者（"])):
            # Intro paragraph
            story.append(Paragraph(stripped, intro_style))

        else:
            story.append(Paragraph(stripped, body_style))

    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E5E7EB")))
    story.append(Spacer(1, 6 * mm))

    # ── Signature info table ────────────────────────────────────────────────
    status = contract.get("status", "draft")
    signer_display = contract.get("signer_name") or "未署名"
    signed_at = contract.get("signed_at") or "—"

    sig_data = [
        [Paragraph("署名者", label_style), Paragraph(signer_display, value_style)],
        [Paragraph("署名日時", label_style), Paragraph(signed_at, value_style)],
        [Paragraph("作成者", label_style), Paragraph(creator_name, value_style)],
        [
            Paragraph("ステータス", label_style),
            Paragraph("締結済み" if status == "signed" else "未署名", value_style),
        ],
    ]
    sig_table = Table(sig_data, colWidths=[35 * mm, None])
    sig_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#F0FDF4"), colors.white]),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#E5E7EB")),
            ]
        )
    )
    story.append(sig_table)

    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E5E7EB")))
    story.append(Spacer(1, 4 * mm))

    # ── Footer ─────────────────────────────────────────────────────────────
    story.append(Paragraph(f"SHA-256: {contract.get('hash', '')}", small_style))
    story.append(Paragraph(
        "このPDFはFitSignによって生成された合意記録です。法的効力については利用規約をご確認ください。",
        small_style
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer
