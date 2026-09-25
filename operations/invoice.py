"""Reports > Generate Invoice.

Pick a client's trips over a date range, tick which ones to bill and which
columns the invoice should carry, and download a PDF with just that."""
from datetime import date
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from masters.models import Client
from .models import Trip

# (key, label, value-from-trip, is a money column that gets totalled)
COLUMNS = [
    ("trip_no", "Trip #", lambda t: t.trip_no, False),
    ("trip_date", "Date", lambda t: t.trip_date, False),
    ("bilty_number", "Bilty #", lambda t: t.bilty_number, False),
    ("vehicle", "Vehicle #", lambda t: t.vehicle.vehicle_number, False),
    ("sub_category", "Sub-Category", lambda t: t.sub_category.name if t.sub_category_id else "", False),
    ("route", "Route", lambda t: t.route.route_code, False),
    ("weight", "Weight (Tons)", lambda t: t.weight, False),
    ("stopover_city", "Stopover City", lambda t: t.stopover_city.name if t.stopover_city_id else "", False),
    ("stopover_charges", "Stopover Charges", lambda t: t.stopover_charges, True),
    ("trip_charges", "Trip Charges", lambda t: t.freight - (t.additional_charges or 0) - (t.stopover_charges or 0), True),
    ("additional_charges", "Additional Charges", lambda t: t.additional_charges, True),
    ("total_freight", "Total Freight", lambda t: t.freight, True),
    ("remarks", "Remarks", lambda t: t.remarks, False),
]
DEFAULT_COLUMNS = ["trip_no", "trip_date", "bilty_number", "route", "weight",
                    "trip_charges", "additional_charges", "total_freight"]


def _client_columns(client):
    """A client without Sub-Categories / Stopover Charges never sees those
    two ticks - there's nothing on their trips to invoice for."""
    cols = COLUMNS
    if not client.has_sub_categories:
        cols = [c for c in cols if c[0] != "sub_category"]
    if not client.has_stopover:
        cols = [c for c in cols if c[0] not in ("stopover_city", "stopover_charges")]
    return cols


@login_required
def invoice_select(request):
    client_id = request.GET.get("client") or ""
    start_date = request.GET.get("start_date") or ""
    end_date = request.GET.get("end_date") or ""
    client = Client.objects.filter(pk=client_id).first() if client_id else None
    trips = []
    if client:
        trips = Trip.objects.filter(client=client).select_related(
            "route", "vehicle", "sub_category", "stopover_city")
        if start_date:
            trips = trips.filter(trip_date__gte=start_date)
        if end_date:
            trips = trips.filter(trip_date__lte=end_date)
        trips = list(trips.order_by("trip_date", "id"))

    columns = _client_columns(client) if client else []
    trip_rows = []
    for t in trips:
        cells = []
        for key, _, fn, money in columns:
            value = fn(t)
            if money:
                cells.append((key, f"{_d(value):,.0f}", True))
            elif hasattr(value, "strftime"):
                cells.append((key, value.strftime("%d-%b-%y"), False))
            else:
                cells.append((key, str(value) if value not in (None, "") else "--", False))
        trip_rows.append({"id": t.id, "total": t.freight, "cells": cells})

    return render(request, "operations/invoice_select.html", {
        "clients": Client.objects.order_by("name"),
        "client": client,
        "start_date": start_date, "end_date": end_date,
        "trip_rows": trip_rows,
        "columns": columns,
        "default_columns": DEFAULT_COLUMNS,
    })


def _d(value):
    return Decimal(str(value or 0))


@login_required
def invoice_generate_pdf(request):
    if request.method != "POST":
        return redirect("invoice_select")

    client = get_object_or_404(Client, pk=request.POST.get("client"))
    trip_ids = request.POST.getlist("trip_ids")
    by_key = {c[0]: c for c in _client_columns(client)}
    cols = [by_key[k] for k in request.POST.getlist("columns") if k in by_key]
    if not cols:
        cols = [by_key[k] for k in DEFAULT_COLUMNS if k in by_key]

    trips = Trip.objects.filter(pk__in=trip_ids, client=client).select_related(
        "route", "vehicle", "sub_category", "stopover_city").order_by("trip_date", "id")

    buffer_ = _build_pdf(client, trips, cols)
    response = HttpResponse(buffer_, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Invoice - {client.name}.pdf"'
    return response


def _build_pdf(client, trips, cols):
    import io
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=10 * mm, rightMargin=10 * mm,
                            topMargin=10 * mm, bottomMargin=10 * mm, title=f"Invoice - {client.name}")
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("AL MURAD LOGISTICS", styles["Title"]),
        Paragraph(f"Invoice - {client.name}", styles["Heading2"]),
        Paragraph(f"Generated on {date.today():%d-%b-%Y} &bull; {len(trips)} trip(s)", styles["Normal"]),
        Spacer(1, 6 * mm),
    ]

    header = [label for _, label, _, _ in cols]
    money_cols = [i for i, (_, _, _, money) in enumerate(cols) if money]
    rows = [header]
    totals = [Decimal(0)] * len(cols)
    for t in trips:
        row = []
        for i, (_, _, fn, money) in enumerate(cols):
            value = fn(t)
            if money:
                value = _d(value)
                totals[i] += value
                row.append(f"{value:,.0f}")
            elif hasattr(value, "strftime"):
                row.append(value.strftime("%d-%b-%y"))
            else:
                row.append(str(value) if value not in (None, "") else "-")
        rows.append(row)

    total_row = [""] * len(cols)
    total_row[0] = "TOTAL"
    for i in money_cols:
        total_row[i] = f"{totals[i]:,.0f}"
    rows.append(total_row)

    table = Table(rows, repeatRows=1)
    table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#9ca3af")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f3f4f6")]),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#d1d5db")),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 14 * mm))
    elements.append(Paragraph("____________________<br/>Authorized Signature", styles["Normal"]))
    doc.build(elements)
    return buffer.getvalue()
