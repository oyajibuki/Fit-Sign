from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont


def _register_fonts():
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))
        pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
        return "HeiseiKakuGo-W5", "HeiseiMin-W3"
    except Exception:
        return "Helvetica-Bold", "Helvetica"


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

    # Styles
    title_style = ParagraphStyle(
        "Title",
        fontName=bold_font,
        fontSize=16,
        leading=22,
        spaceAfter=4,
        textColor=colors.HexColor("#111827"),
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        fontName=normal_font,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#6B7280"),
        spaceAfter=12,
    )
    body_style = ParagraphStyle(
        "Body",
        fontName=normal_font,
        fontSize=10,
        leading=18,
        textColor=colors.HexColor("#1F2937"),
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

    # Header
    template_emoji = contract.get("template_emoji", "📋")
    template_name = contract.get("template_name", "契約書")
    story.append(Paragraph(f"{template_name}", title_style))
    story.append(Paragraph(f"FitSign 合意記録  |  契約ID: {contract.get('id', '')}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#111827")))
    story.append(Spacer(1, 6 * mm))

    # Contract body
    body_template = contract.get("template_body", "")
    body_text = body_template.format(
        content=contract.get("content", ""),
        amount=contract.get("amount", ""),
        contract_date=contract.get("contract_date", ""),
    )
    for line in body_text.split("\n"):
        story.append(Paragraph(line if line.strip() else "&nbsp;", body_style))

    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E5E7EB")))
    story.append(Spacer(1, 6 * mm))

    # Signature info table
    status = contract.get("status", "draft")
    signer_name = contract.get("signer_name") or "未署名"
    signed_at = contract.get("signed_at") or "—"

    sig_data = [
        [Paragraph("署名者", label_style), Paragraph(signer_name, value_style)],
        [Paragraph("署名日時", label_style), Paragraph(signed_at, value_style)],
        [Paragraph("作成者ID", label_style), Paragraph(contract.get("creator_id", ""), value_style)],
        [
            Paragraph("ステータス", label_style),
            Paragraph("✅ 締結済み" if status == "signed" else "⏳ 未署名", value_style),
        ],
    ]
    sig_table = Table(sig_data, colWidths=[35 * mm, None])
    sig_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#F9FAFB"), colors.white]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(sig_table)

    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E5E7EB")))
    story.append(Spacer(1, 4 * mm))

    # Hash footer
    story.append(Paragraph(f"SHA-256: {contract.get('hash', '')}", small_style))
    story.append(Paragraph("このPDFはFitSignによって生成された合意記録です。法的効力については利用規約をご確認ください。", small_style))

    doc.build(story)
    buffer.seek(0)
    return buffer
