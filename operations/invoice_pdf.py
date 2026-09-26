"""PDF versions of the two invoice templates - the same layout as the Excel
files in invoice_xlsx.py (Segoe UI isn't available to reportlab, so Helvetica).

  * Tax invoice     -> page 1 "Invoice" (portrait) + page 2 "Trips Summary" (landscape)
  * Non-tax invoice -> one landscape page "NON-TAX INVOICE"
"""
import io
from decimal import Decimal
from xml.sax.saxutils import escape as e

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.platypus import (
    BaseDocTemplate, Frame, NextPageTemplate, PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle,
)

BLUE, LIGHT, TEXT, GREY, FOOT = (colors.HexColor(x) for x in ("#1F4E78", "#F3F6F9", "#1F2937", "#A6A6A6", "#666666"))
_BASE = ParagraphStyle("base", fontName="Helvetica", fontSize=9, leading=11, textColor=TEXT)


def _st(size, bold=False, italic=False, color=TEXT, align=0, leading=None):
    font = "Helvetica" + ("-BoldOblique" if bold and italic else "-Bold" if bold else "-Oblique" if italic else "")
    return ParagraphStyle(f"s{size}{bold}{italic}{align}", parent=_BASE, fontName=font, fontSize=size,
                          leading=leading or size * 1.25, textColor=color, alignment=align)


WHITE_B = lambda size, align=0: _st(size, True, color=colors.white, align=align)


class _NumberedCanvas(pdf_canvas.Canvas):
    """Draws 'Page x of y' at the bottom of every page, like the template's footer."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved)
        for state in self._saved:
            self.__dict__.update(state)
            self.setFont("Helvetica-Oblique", 8)
            self.setFillColor(FOOT)
            self.drawCentredString(self._pagesize[0] / 2, 6 * mm, f"Page {self._pageNumber} of {total}")
            super().showPage()
        super().save()


def _bar(left, right, width, size, height, right_size=8):
    if right is None:
        t = Table([[Paragraph(e(left), WHITE_B(size))]], colWidths=[width], rowHeights=[height])
    else:
        t = Table([[Paragraph(e(left), WHITE_B(size)), Paragraph(e(right), WHITE_B(right_size, 2))]],
                  colWidths=[width - 60 * mm, 60 * mm], rowHeights=[height])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), BLUE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("LEFTPADDING", (0, 0), (0, 0), 8), ("RIGHTPADDING", (-1, 0), (-1, 0), 8)]))
    return t


def _party(p, name_size):
    lines = [f'<font size="{name_size}">{e(p["name"])}</font>']
    if p["address"]:
        lines.append(f'<font size="8">{e(p["address"]).replace(chr(10), "<br/>")}</font>')
    ids = "    ".join(x for x in (f'NTN: {e(p["ntn"])}' if p["ntn"] else "", f'STRN: {e(p["strn"])}' if p["strn"] else "") if x)
    if ids:
        lines.append(f'<font size="8">{ids}</font>')
    return Paragraph("<br/>".join(lines), _st(9, leading=11))


def _parties(data, width, name_size, head_size, body_height):
    half = width / 2
    t = Table([[Paragraph("BILL TO / CUSTOMER", WHITE_B(head_size)), Paragraph("SERVICE PROVIDER", WHITE_B(head_size))],
               [_party(data["bill_to"], name_size), _party(data["provider"], name_size)]],
              colWidths=[half, half], rowHeights=[None, body_height])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), BLUE), ("GRID", (0, 0), (-1, -1), 0.4, GREY),
                           ("VALIGN", (0, 0), (-1, 0), "MIDDLE"), ("VALIGN", (0, 1), (-1, 1), "TOP"),
                           ("TOPPADDING", (0, 0), (-1, 0), 5), ("BOTTOMPADDING", (0, 0), (-1, 0), 5)]))
    return t


def _info(data, width):
    labels = ("Invoice Date", "Billing Period", "Payment Terms", "Due Date", "Invoice #")
    values = (f"{data['invoice_date']:%d %b %Y}", data["period"], f"{data['payment_days']} Days",
              f"{data['due_date']:%d %b %Y}", data["invoice_no"])
    t = Table([[Paragraph(x, _st(8.5, True)) for x in labels], [Paragraph(e(x), _st(9.5)) for x in values]],
              colWidths=[width * r for r in (0.17, 0.21, 0.17, 0.17, 0.28)])
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.4, GREY), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return t


def _total_bar(label, amount, width, label_size, amount_size, height):
    t = Table([[Paragraph(e(label), _st(label_size, True)), Paragraph(f"{amount:,.0f}", _st(amount_size, True, color=BLUE, align=2))]],
              colWidths=[width - 50 * mm, 50 * mm], rowHeights=[height])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), LIGHT), ("LINEABOVE", (0, 0), (-1, 0), 1.4, BLUE),
                           ("LINEBELOW", (0, 0), (-1, 0), 1.4, BLUE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("LEFTPADDING", (0, 0), (0, 0), 8), ("RIGHTPADDING", (-1, 0), (-1, 0), 8)]))
    return t


def _words(data, width):
    t = Table([[Paragraph("AMOUNT IN WORDS", _st(8.5, True)), Paragraph(e(data["in_words"]), _st(9.5, italic=True))]],
              colWidths=[34 * mm, width - 34 * mm])
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.4, GREY), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    return t


def _notes(lines, width):
    rows = [[Paragraph("NOTES", WHITE_B(9.5))]] + [[Paragraph("• " + e(line), _st(8.5))] for line in lines]
    t = Table(rows, colWidths=[width])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), BLUE), ("LINEBELOW", (0, 1), (-1, -1), 0.4, GREY),
                           ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                           ("LEFTPADDING", (0, 0), (-1, -1), 6)]))
    return t


def _trips_table(data, width):
    money = [False] + data["money"]
    head = [Paragraph("S.no", WHITE_B(8))] + [Paragraph(e(h), WHITE_B(8, 2 if m else 0)) for h, m in zip(data["headers"], money[1:])]
    body = [head]
    for n, row in enumerate(data["rows"], start=1):
        cells = [Paragraph(str(n), _st(8))]
        for value, m in zip(row, money[1:]):
            if m:
                text, align = (f"{value:,.2f}" if value else "-"), 2
            elif hasattr(value, "strftime"):
                text, align = value.strftime("%d-%b-%y"), 0
            elif isinstance(value, Decimal):
                text, align = f"{value:,.2f}", 0
            else:
                text, align = ("" if value in (None, "") else str(value)), 0
            cells.append(Paragraph(e(text), _st(8, align=align)))
        body.append(cells)
    n_cols = len(head)
    first_money = next((i for i, m in enumerate(money) if m), n_cols)
    foot = [Paragraph("TOTAL", _st(9, True))] + [""] * (n_cols - 1)
    for i in data["money_idx"]:
        foot[i + 1] = Paragraph(f"{data['totals'][i]:,.2f}", _st(9, True, align=2))
    body.append(foot)
    widths = [11 * mm] + [(width - 11 * mm) / max(n_cols - 1, 1)] * (n_cols - 1)
    t = Table(body, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE), ("GRID", (0, 0), (-1, -2), 0.4, GREY), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, -1), (-1, -1), LIGHT), ("LINEABOVE", (0, -1), (-1, -1), 1.4, BLUE), ("LINEBELOW", (0, -1), (-1, -1), 1.4, BLUE),
        ("SPAN", (0, -1), (max(first_money - 1, 0), -1)), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def _meta(data, width):
    t = Table([[Paragraph(x, _st(9, True)) for x in ("Invoice #", "Billing Period", "Customer", "Service Provider")],
               [Paragraph(e(x), _st(9.5)) for x in (data["invoice_no"], data["period"], data["bill_to"]["name"], data["provider"]["name"])]],
              colWidths=[width / 4] * 4)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, GREY), ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
                           ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    return t


def _tax_pdf(data):
    buf = io.BytesIO()
    doc = BaseDocTemplate(buf, pagesize=A4, title=f"Invoice {data['invoice_no']}")
    w1, land = A4[0] - 30 * mm, landscape(A4)
    w2 = land[0] - 20 * mm
    doc.addPageTemplates([
        PageTemplate(id="P", pagesize=A4, frames=[Frame(15 * mm, 15 * mm, w1, A4[1] - 30 * mm, id="p")]),
        PageTemplate(id="L", pagesize=land, frames=[Frame(10 * mm, 12 * mm, w2, land[1] - 22 * mm, id="l")]),
    ])
    els = [_bar("SALES TAX INVOICE", f"SALES TAX no. {data['sales_tax_no']}".strip(), w1, 18, 12 * mm), Spacer(1, 4 * mm),
           _info(data, w1), Spacer(1, 5 * mm), _parties(data, w1, 14, 9, 30 * mm), Spacer(1, 5 * mm)]

    desc = Table([[Paragraph("DESCRIPTION OF SERVICES", WHITE_B(8.5)), Paragraph("AMOUNT (PKR)", WHITE_B(8.5, 2))],
                  [Paragraph("Transportation Services", _st(9.5)), Paragraph(f"{data['subtotal']:,.0f}", _st(9.5, align=2))]],
                 colWidths=[w1 - 50 * mm, 50 * mm], rowHeights=[None, 11 * mm])
    desc.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), BLUE), ("GRID", (0, 0), (-1, -1), 0.4, GREY),
                              ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, 0), 4), ("BOTTOMPADDING", (0, 0), (-1, 0), 4)]))
    els += [desc, Spacer(1, 5 * mm)]

    if data["breakdown"]:
        head = [Paragraph("TAX JURISDICTION", WHITE_B(7.5)), Paragraph("TAX RATE", WHITE_B(7.5, 1)),
                Paragraph("TAXABLE AMOUNT (PKR)", WHITE_B(7.5, 1)), Paragraph("TAX AMOUNT (PKR)", WHITE_B(7.5, 2))]
        rows = [head]
        for label, rate, base, amount in data["breakdown"]:
            short = "KPK" if label.startswith("KPK") else label
            rows.append([Paragraph(e(short), _st(9.5)), Paragraph(format(rate.normalize(), "f") + "%", _st(9.5, align=2)),
                         Paragraph(f"{base:,.0f}" if base else "-", _st(9.5, align=2)), Paragraph(f"{amount:,.0f}" if amount else "-", _st(9.5, align=2))])
        tax = Table(rows, colWidths=[w1 * 0.4, w1 * 0.2, w1 * 0.2, w1 * 0.2])
        tax.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), BLUE), ("GRID", (0, 0), (-1, -1), 0.4, GREY),
                                 ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
        els += [tax, Spacer(1, 6 * mm)]

    els += [_total_bar("TOTAL INVOICE AMOUNT (INCL. SALES TAX)", data["grand_total"], w1, 11, 12, 13 * mm), Spacer(1, 6 * mm),
            _words(data, w1), Spacer(1, 5 * mm), _notes(data["notes"], w1)]

    els += [NextPageTemplate("L"), PageBreak(), _bar("TRIPS SUMMARY", None, w2, 18, 12 * mm), Spacer(1, 4 * mm),
            _meta(data, w2), Spacer(1, 4 * mm), _trips_table(data, w2)]
    doc.build(els, canvasmaker=_NumberedCanvas)
    return buf.getvalue()


def _nontax_pdf(data):
    buf = io.BytesIO()
    land = landscape(A4)
    doc = BaseDocTemplate(buf, pagesize=land, title=f"Invoice {data['invoice_no']}")
    w = land[0] - 20 * mm
    doc.addPageTemplates([PageTemplate(id="L", pagesize=land, frames=[Frame(10 * mm, 12 * mm, w, land[1] - 22 * mm, id="l")])])
    notes = [n for n in data["notes"] if "Page 2" not in n]  # a single page has no Page 2
    els = [_parties(data, w, 16, 12, 24 * mm), Spacer(1, 4 * mm), _info(data, w), Spacer(1, 4 * mm),
           _bar("TRIPS SUMMARY", None, w, 15, 10 * mm), Spacer(1, 2 * mm), _trips_table(data, w), Spacer(1, 5 * mm),
           _total_bar("TOTAL INVOICE AMOUNT", data["grand_total"], w, 11, 12, 12 * mm), Spacer(1, 5 * mm),
           _words(data, w), Spacer(1, 5 * mm), _notes(notes, w)]
    doc.build(els, canvasmaker=_NumberedCanvas)
    return buf.getvalue()


def build(data):
    return _tax_pdf(data) if data["tax_enabled"] else _nontax_pdf(data)
