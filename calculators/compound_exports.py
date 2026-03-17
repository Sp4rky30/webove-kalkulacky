import csv
import io
from pathlib import Path

from flask import make_response, send_file
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .compound_interest import calculate_compound_data
from .formatting import format_czk

PDF_FONT_NAME = "ArialUnicode"
PDF_FONT_PATHS = (
    Path("/Library/Fonts/Arial Unicode.ttf"),
    Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
)


def register_pdf_font() -> str:
    if PDF_FONT_NAME in pdfmetrics.getRegisteredFontNames():
        return PDF_FONT_NAME
    for font_path in PDF_FONT_PATHS:
        if font_path.exists():
            pdfmetrics.registerFont(TTFont(PDF_FONT_NAME, str(font_path)))
            return PDF_FONT_NAME
    raise RuntimeError("Nepodařilo se najít Unicode font pro PDF export.")


def build_compound_csv_response(inputs):
    data = calculate_compound_data(**inputs)
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Rok", "Celkem vlozeno", "Celkova hodnota", "Zisk", "Realna hodnota"])
    for row in data:
        writer.writerow([row["year"], f"{row['deposits']:.2f}", f"{row['total']:.2f}", f"{row['profit']:.2f}", f"{row['real_total']:.2f}"])

    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = "attachment; filename=slozene-uroceni.csv"
    return response


def build_compound_pdf_response(inputs):
    data = calculate_compound_data(**inputs)
    pdf_font_name = register_pdf_font()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    styles["Title"].fontName = pdf_font_name
    styles["BodyText"].fontName = pdf_font_name
    story = [Paragraph("Kalkulačka složeného úročení", styles["Title"]), Spacer(1, 12)]
    story.append(
        Paragraph(
            (
                f"Začáteční vklad: {format_czk(inputs['initial_deposit'])}<br/>"
                f"Roční úrok: {inputs['annual_rate']} %<br/>"
                f"Měsíční vklad: {format_czk(inputs['monthly_deposit'])}<br/>"
                f"Inflace: {inputs['inflation_rate']} %<br/>"
                f"Počet let: {inputs['years']}"
            ),
            styles["BodyText"],
        )
    )
    story.append(Spacer(1, 16))

    table_data = [["Rok", "Celkem vloženo", "Celková hodnota", "Zisk", "Reálná hodnota"]]
    for row in data:
        if row["year"] == 0 or row["year"] % 5 == 0 or row["year"] == inputs["years"]:
            table_data.append([str(row["year"]), format_czk(row["deposits"]), format_czk(row["total"]), format_czk(row["profit"]), format_czk(row["real_total"])])

    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                ("FONTNAME", (0, 0), (-1, -1), pdf_font_name),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#f8fafc")]),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table)
    doc.build(story)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="slozene-uroceni.pdf", mimetype="application/pdf")
