"""PDF versions of the two invoice templates - the same layout as the Excel
files in invoice_xlsx.py (Segoe UI isn't available to reportlab, so Helvetica).

  * Tax invoice     -> page 1 "Invoice" + page 2 "Trips Summary"
  * Non-tax invoice -> one page "NON-TAX INVOICE"

Everything is A4 portrait with room left at the top and bottom for the
company letterhead the invoices are printed on. The trips table is set in the
largest font that still fits its page (one page for the non-tax invoice, page
2 for the tax invoice), every row the same height, Remarks wrapped in full.
"""
import io
from decimal import Decimal
from xml.sax.saxutils import escape as e

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle,
)

BLUE, LIGHT, TEXT, GREY, FOOT = (colors.HexColor(x) for x in ("#1F4E78", "#F3F6F9", "#1F2937", "#A6A6A6", "#666666"))
_BASE = ParagraphStyle("base", fontName="Helvetica", fontSize=9, leading=11, textColor=TEXT)


def _st(size, bold=False, italic=False, color=TEXT, align=0, leading=None):
    font = "Helvetica" + ("-BoldOblique" if bold and italic else "-Bold" if bold else "-Oblique" if italic else "")
    return ParagraphStyle(f"s{size}{bold}{italic}{align}", parent=_BASE, fontName=font, fontSize=size,
                          leading=leading or size * 1.25, textColor=color, alignment=align)


WHITE_B = lambda size, align=0: _st(size, True, color=colors.white, align=align)

# Letterhead-safe page: the printed letterhead's header/footer sit in these margins.
TOP_MARGIN, BOTTOM_MARGIN, SIDE_MARGIN = 40 * mm, 25 * mm, 12 * mm
PAGE_W = A4[0] - 2 * SIDE_MARGIN
PAGE_H = A4[1] - TOP_MARGIN - BOTTOM_MARGIN
# Trips table font sizes tried, largest first, until the table fits its page.
FONT_STEPS = (9.5, 9, 8.5, 8, 7.5, 7, 6.5, 6)


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
            # just under the text area, above the letterhead's footer
            self.drawCentredString(self._pagesize[0] / 2, BOTTOM_MARGIN - 6 * mm, f"Page {self._pageNumber} of {total}")
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
                           ("TOPPADDING", (0, 0), (-1, 0), 5), ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
                           ("TOPPADDING", (0, 1), (-1, 1), 4), ("BOTTOMPADDING", (0, 1), (-1, 1), 6)]))
    return t


def _info(data, width):
    labels = ("Invoice Date", "Billing Period", "Payment Terms", "Due Date", "Invoice #")
    values = (f"{data['invoice_date']:%d %b %Y}", data["period"], f"{data['payment_days']} Days",
              f"{data['due_date']:%d %b %Y}", data["invoice_no"])
    t = Table([[Paragraph(x, _st(8.5, True)) for x in labels], [Paragraph(e(x), _st(9.5)) for x in values]],
              colWidths=[width * r for r in (0.16, 0.26, 0.15, 0.16, 0.27)])
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


# Trips table layout: every column is as wide as its values (one line) and its header
# (which may wrap at spaces) need; Remarks takes all the width left over and wraps onto
# at most two lines. A long remark is first set up to 2 pt smaller to stay on one
# line; all trip rows are the same height (one line, or two if any remark still
# needs it).
_PAD = 2.5          # left/right cell padding (pt)
_VPAD = 1.6         # top/bottom cell padding (pt)
_MIN_REMARKS = 30 * mm
_MIN_REMARK_FONT = 5


def _cell_text(value, money):
    if money:
        return (f"{value:,.2f}" if value else "-"), 2
    if hasattr(value, "strftime"):
        return value.strftime("%d-%b-%y"), 0
    if isinstance(value, Decimal):
        return f"{value:,.2f}", 0
    return ("" if value in (None, "") else str(value)), 0


def _lines(para, width):
    para.wrap(width, 10000)
    return len(para.blPara.lines)


def _trips_table(data, width, fs, strict=True):
    """The trips table at font size `fs`, or None if at this size the columns
    don't fit the page width without breaking a number / date / code
    (strict=False squeezes them in anyway - the last resort for very wide tables)."""
    money = [False] + data["money"]
    keys = ["sno"] + data["keys"]
    headers = ["S.no"] + data["headers"]
    rows_text = [[(str(n), 0)] + [_cell_text(v, m) for v, m in zip(row, money[1:])]
                 for n, row in enumerate(data["rows"], start=1)]
    total_text = {i + 1: f"{data['totals'][i]:,.2f}" for i in data["money_idx"]}
    remarks = keys.index("remarks") if "remarks" in keys else None

    # natural width of every column but Remarks
    widths = []
    for i, key in enumerate(keys):
        if i == remarks:
            widths.append(0)
            continue
        head_word = max((stringWidth(w, "Helvetica-Bold", fs) for w in headers[i].split()), default=0)
        value = max((stringWidth(r[i][0], "Helvetica", fs) for r in rows_text), default=0)
        foot = stringWidth(total_text.get(i, ""), "Helvetica-Bold", fs + 0.5)
        widths.append(max(head_word, value, foot) + 2 * _PAD + 1)
    used = sum(widths)
    if remarks is not None:
        if width - used < _MIN_REMARKS:
            if strict:
                return None
            widths = [w * (width - _MIN_REMARKS) / used for w in widths]
            used = width - _MIN_REMARKS
        # Remarks: what its longest remark needs on one line (at least the minimum),
        # up to all the width left; any spare is spread over every column.
        longest = max((stringWidth(r[remarks][0], "Helvetica", fs) for r in rows_text), default=0) + 2 * _PAD + 1
        widths[remarks] = min(width - used, max(longest, _MIN_REMARKS))
        used = sum(widths)
    elif used > width:
        if strict:
            return None
    widths = [w * width / used for w in widths]  # fill the page width exactly

    lead = fs * 1.2
    style = lambda f, a=0, bold=False: _st(f, bold, align=a, leading=f * 1.2)
    head = [Paragraph(e(h), WHITE_B(fs, 2 if m else 0)) for h, m in zip(headers, money)]
    body_rows, two_lines = [], False
    for cells in rows_text:
        row = []
        for i, (text, align) in enumerate(cells):
            if i == remarks and text:
                inner = widths[i] - 2 * _PAD
                # one line if a slightly smaller font gets it there, else two lines
                f = fs
                para = Paragraph(e(text), style(f))
                while _lines(para, inner) > 1 and f - 0.5 >= max(fs - 2, _MIN_REMARK_FONT):
                    f -= 0.5
                    para = Paragraph(e(text), style(f))
                if _lines(para, inner) > 1:
                    f = fs
                    para = Paragraph(e(text), style(f))
                    while _lines(para, inner) > 2 and f > _MIN_REMARK_FONT:
                        f -= 0.5
                        para = Paragraph(e(text), style(f))
                    two_lines = True
                row.append(para)
            else:
                row.append(Paragraph(e(text), style(fs, align)))
        body_rows.append(row)
    n_cols = len(head)
    first_money = next((i for i, m in enumerate(money) if m), n_cols)
    foot = [Paragraph("TOTAL", _st(fs + 0.5, True))] + [""] * (n_cols - 1)
    for i, text in total_text.items():
        foot[i] = Paragraph(text, _st(fs + 0.5, True, align=2))

    head_h = max(p.wrap(w - 2 * _PAD, 1000)[1] for p, w in zip(head, widths)) + 2 * _VPAD + 1
    row_h = lead * (2 if two_lines else 1) + 2 * _VPAD
    heights = [head_h] + [row_h] * len(body_rows) + [lead + 2 * _VPAD + 2]

    t = Table([head] + body_rows + [foot], colWidths=widths, rowHeights=heights, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE), ("GRID", (0, 0), (-1, -2), 0.4, GREY), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, -1), (-1, -1), LIGHT), ("LINEABOVE", (0, -1), (-1, -1), 1.4, BLUE), ("LINEBELOW", (0, -1), (-1, -1), 1.4, BLUE),
        ("SPAN", (0, -1), (max(first_money - 1, 0), -1)), ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), _PAD), ("RIGHTPADDING", (0, 0), (-1, -1), _PAD),
    ]))
    return t


def _fitted(build_pages, max_pages):
    """Build with the largest trips-table font that keeps the document within
    `max_pages` (and every number on one line); if even the smallest spills
    over, use the smallest that fits the width and let the table run on."""
    fallback = None
    for fs in FONT_STEPS:
        result = build_pages(fs)
        if result is None:
            continue
        pdf, pages = result
        fallback = pdf
        if pages <= max_pages:
            return pdf
    return fallback if fallback is not None else build_pages(None)[0]


def _meta(data, width):
    t = Table([[Paragraph(x, _st(9, True)) for x in ("Invoice #", "Billing Period", "Customer", "Service Provider")],
               [Paragraph(e(x), _st(9.5)) for x in (data["invoice_no"], data["period"], data["bill_to"]["name"], data["provider"]["name"])]],
              colWidths=[width / 4] * 4)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, GREY), ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
                           ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    return t


def _doc(buf, title):
    doc = BaseDocTemplate(buf, pagesize=A4, title=title, leftMargin=SIDE_MARGIN, rightMargin=SIDE_MARGIN,
                          topMargin=TOP_MARGIN, bottomMargin=BOTTOM_MARGIN)
    doc.addPageTemplates([PageTemplate(id="P", pagesize=A4,
                                       frames=[Frame(SIDE_MARGIN, BOTTOM_MARGIN, PAGE_W, PAGE_H, id="p",
                                                     leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)])])
    return doc


def _render(title, elements):
    buf = io.BytesIO()
    doc = _doc(buf, title)
    doc.build(elements, canvasmaker=_NumberedCanvas)
    return buf.getvalue(), doc.page


def _tax_first_page(data):
    w = PAGE_W
    first = [_bar("SALES TAX INVOICE", f"SALES TAX no. {data['sales_tax_no']}".strip(), w, 16, 11 * mm), Spacer(1, 4 * mm),
             _info(data, w), Spacer(1, 5 * mm), _parties(data, w, 13, 9, 28 * mm), Spacer(1, 5 * mm)]

    desc = Table([[Paragraph("DESCRIPTION OF SERVICES", WHITE_B(8.5)), Paragraph("AMOUNT (PKR)", WHITE_B(8.5, 2))],
                  [Paragraph("Transportation Services", _st(9.5)), Paragraph(f"{data['subtotal']:,.0f}", _st(9.5, align=2))]],
                 colWidths=[w - 50 * mm, 50 * mm], rowHeights=[None, 10 * mm])
    desc.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), BLUE), ("GRID", (0, 0), (-1, -1), 0.4, GREY),
                              ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, 0), 4), ("BOTTOMPADDING", (0, 0), (-1, 0), 4)]))
    first += [desc, Spacer(1, 5 * mm)]

    if data["breakdown"]:
        head = [Paragraph("TAX JURISDICTION", WHITE_B(7.5)), Paragraph("TAX RATE", WHITE_B(7.5, 1)),
                Paragraph("TAXABLE AMOUNT (PKR)", WHITE_B(7.5, 1)), Paragraph("TAX AMOUNT (PKR)", WHITE_B(7.5, 2))]
        rows = [head]
        for label, rate, base, amount in data["breakdown"]:
            short = "KPK" if label.startswith("KPK") else label
            rows.append([Paragraph(e(short), _st(9.5)), Paragraph(format(rate.normalize(), "f") + "%", _st(9.5, align=2)),
                         Paragraph(f"{base:,.0f}" if base else "-", _st(9.5, align=2)), Paragraph(f"{amount:,.0f}" if amount else "-", _st(9.5, align=2))])
        tax = Table(rows, colWidths=[w * 0.4, w * 0.2, w * 0.2, w * 0.2])
        tax.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), BLUE), ("GRID", (0, 0), (-1, -1), 0.4, GREY),
                                 ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
        first += [tax, Spacer(1, 5 * mm)]

    first += [_total_bar("TOTAL INVOICE AMOUNT (INCL. SALES TAX)", data["grand_total"], w, 11, 12, 12 * mm), Spacer(1, 5 * mm),
              _words(data, w), Spacer(1, 5 * mm), _notes(data["notes"], w)]
    return first


def _tax_pdf(data):
    w = PAGE_W

    def attempt(fs):
        table = _trips_table(data, w, fs or FONT_STEPS[-1])
        if table is None and fs is not None:
            return None
        if table is None:  # nothing fits on one line even at the smallest size - let it wrap
            return _render(f"Invoice {data['invoice_no']}", _tax_first_page(data) + [PageBreak(), _bar("TRIPS SUMMARY", None, w, 16, 11 * mm),
                           Spacer(1, 4 * mm), _meta(data, w), Spacer(1, 4 * mm), _trips_table(data, w, FONT_STEPS[-1], strict=False)])
        return _render(f"Invoice {data['invoice_no']}", _tax_first_page(data) + [PageBreak(), _bar("TRIPS SUMMARY", None, w, 16, 11 * mm),
                       Spacer(1, 4 * mm), _meta(data, w), Spacer(1, 4 * mm), table])
    return _fitted(attempt, 2)


def _nontax_pdf(data):
    w = PAGE_W
    notes = [n for n in data["notes"] if "Page 2" not in n]  # a single page has no Page 2

    def attempt(fs):
        table = _trips_table(data, w, fs or FONT_STEPS[-1])
        if table is None:
            if fs is not None:
                return None
            table = _trips_table(data, w, FONT_STEPS[-1], strict=False)
        els = [_parties(data, w, 13, 10, None), Spacer(1, 3 * mm), _info(data, w), Spacer(1, 3 * mm),
               _bar("TRIPS SUMMARY", None, w, 12, 8 * mm), Spacer(1, 2 * mm), table, Spacer(1, 3 * mm),
               _total_bar("TOTAL INVOICE AMOUNT", data["grand_total"], w, 11, 12, 10 * mm), Spacer(1, 3 * mm),
               _words(data, w), Spacer(1, 3 * mm), _notes(notes, w)]
        return _render(f"Invoice {data['invoice_no']}", els)
    return _fitted(attempt, 1)


def build(data):
    return _tax_pdf(data) if data["tax_enabled"] else _nontax_pdf(data)
