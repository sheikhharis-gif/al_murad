"""Invoicing > Generate Invoice / Invoices Status.

Pick a client's trips over a date range, tick which ones to bill and which
columns the invoice should carry, optionally work out province-wise tax, and
download a PDF with just that. Every PDF generated is logged as a
GeneratedInvoice (client, company, trips, columns, tax settings, totals) so
Invoices Status can list them, track a status on each, and rebuild the exact
same PDF again on demand - the PDF itself is never stored."""
import io
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

from masters.models import Client, Company, TaxSettings
from .models import GeneratedInvoice, Trip

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

# The 4 provinces Full tax mode charges by - keyed the same as City.province.
TAX_PROVINCES = [("SINDH", "Sindh"), ("PUNJAB", "Punjab"),
                  ("BALOCHISTAN", "Balochistan"), ("KPK", "Khyber Pakhtunkhwa")]


def _client_columns(client):
    """A client without Sub-Categories / Stopover Charges never sees those
    two ticks - there's nothing on their trips to invoice for."""
    cols = COLUMNS
    if not client.has_sub_categories:
        cols = [c for c in cols if c[0] != "sub_category"]
    if not client.has_stopover:
        cols = [c for c in cols if c[0] not in ("stopover_city", "stopover_charges")]
    return cols


def _d(value):
    return Decimal(str(value or 0))


@login_required
def invoice_select(request):
    client_id = request.GET.get("client") or ""
    start_date = request.GET.get("start_date") or ""
    end_date = request.GET.get("end_date") or ""
    client = Client.objects.filter(pk=client_id).first() if client_id else None
    trips = []
    if client:
        trips = Trip.objects.filter(client=client).select_related(
            "route__origin", "route__destination", "vehicle", "sub_category", "stopover_city")
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
        "companies": Company.objects.filter(is_active=True).order_by("name"),
        "client": client,
        "start_date": start_date, "end_date": end_date,
        "trip_rows": trip_rows,
        "columns": columns,
        "default_columns": DEFAULT_COLUMNS,
        "tax_provinces": TAX_PROVINCES,
        "tax_settings": TaxSettings.current(),
    })


def _tax_inputs(post):
    """Generate Invoice's Tax card only switches On/Off and Full/Partial -
    the actual % rates come from the Tax menu's saved TaxSettings, not typed
    per invoice. A snapshot of whichever rates applied is still returned, so
    it can be stored on the GeneratedInvoice and used again on redownload
    even if the settings are later changed."""
    enabled = post.get("tax_enabled") == "on"
    mode = post.get("tax_mode") if post.get("tax_mode") in ("FULL", "PARTIAL") else ""
    if not enabled or not mode:
        return False, "", {}
    settings_obj = TaxSettings.current()
    if mode == "FULL":
        rates = {
            "SINDH": settings_obj.sindh_percent, "PUNJAB": settings_obj.punjab_percent,
            "BALOCHISTAN": settings_obj.balochistan_percent, "KPK": settings_obj.kpk_percent,
        }
    else:
        rates = {"origin": settings_obj.origin_percent, "destination": settings_obj.destination_percent}
    return True, mode, {k: str(v) for k, v in rates.items()}


def _compute_tax(trips, tax_enabled, tax_mode, tax_rates):
    """Returns (subtotal, tax_amount, breakdown) where breakdown is a list of
    (label, rate%, taxable base, tax amount) rows for the PDF's tax summary.

    Full: each trip's whole amount is taxed at its ROUTE'S ORIGIN CITY's own
    province rate (a trip whose origin city has no province set, e.g.
    Islamabad, pays no tax). Partial: every trip is split 50/50, taxed at a
    flat Origin% / Destination% regardless of province."""
    subtotal = sum((_d(t.freight) for t in trips), Decimal(0))
    if not tax_enabled:
        return subtotal, Decimal(0), []

    rates = {k: _d(v) for k, v in tax_rates.items()}
    if tax_mode == "FULL":
        base_by_province = {code: Decimal(0) for code, _ in TAX_PROVINCES}
        unmapped = Decimal(0)
        for t in trips:
            province = t.route.origin.province if t.route_id and t.route.origin_id else ""
            if province in base_by_province:
                base_by_province[province] += _d(t.freight)
            else:
                unmapped += _d(t.freight)
        breakdown = []
        tax_amount = Decimal(0)
        for code, label in TAX_PROVINCES:
            base = base_by_province[code]
            rate = rates.get(code, Decimal(0))
            if base or rate:
                amount = (base * rate / 100).quantize(Decimal("0.01"))
                tax_amount += amount
                breakdown.append((label, rate, base, amount))
        if unmapped:
            breakdown.append(("No Province Set (0%)", Decimal(0), unmapped, Decimal(0)))
        return subtotal, tax_amount, breakdown

    # PARTIAL
    origin_rate = rates.get("origin", Decimal(0))
    dest_rate = rates.get("destination", Decimal(0))
    half_base = (subtotal / 2).quantize(Decimal("0.01"))
    origin_tax = (half_base * origin_rate / 100).quantize(Decimal("0.01"))
    dest_tax = (half_base * dest_rate / 100).quantize(Decimal("0.01"))
    breakdown = [
        ("Origin", origin_rate, half_base, origin_tax),
        ("Destination", dest_rate, half_base, dest_tax),
    ]
    return subtotal, origin_tax + dest_tax, breakdown


@login_required
def invoice_generate_pdf(request):
    if request.method != "POST":
        return redirect("invoice_select")

    client = get_object_or_404(Client, pk=request.POST.get("client"))
    company = get_object_or_404(Company, pk=request.POST.get("company"))
    trip_ids = request.POST.getlist("trip_ids")
    by_key = {c[0]: c for c in _client_columns(client)}
    col_keys = [k for k in request.POST.getlist("columns") if k in by_key]
    if not col_keys:
        col_keys = [k for k in DEFAULT_COLUMNS if k in by_key]
    cols = [by_key[k] for k in col_keys]

    trips = list(Trip.objects.filter(pk__in=trip_ids, client=client).select_related(
        "route__origin", "route__destination", "vehicle", "sub_category", "stopover_city").order_by("trip_date", "id"))

    tax_enabled, tax_mode, tax_rates = _tax_inputs(request.POST)
    subtotal, tax_amount, breakdown = _compute_tax(trips, tax_enabled, tax_mode, tax_rates)
    grand_total = subtotal + tax_amount

    invoice = GeneratedInvoice.objects.create(
        client=client, company=company, columns=col_keys,
        tax_enabled=tax_enabled, tax_mode=tax_mode, tax_rates=tax_rates,
        subtotal=subtotal, tax_amount=tax_amount, grand_total=grand_total,
        created_by=request.user if request.user.is_authenticated else None,
    )
    invoice.trips.set(trips)

    pdf_bytes = _build_pdf(invoice, client, company, trips, cols, tax_enabled, tax_mode, subtotal, tax_amount, breakdown)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Invoice {invoice.invoice_no} - {client.name}.pdf"'
    return response


@login_required
def invoice_redownload(request, invoice_id):
    invoice = get_object_or_404(GeneratedInvoice, pk=invoice_id)
    trips = list(invoice.trips.select_related(
        "route__origin", "route__destination", "vehicle", "sub_category", "stopover_city").order_by("trip_date", "id"))
    by_key = {c[0]: c for c in _client_columns(invoice.client)}
    cols = [by_key[k] for k in invoice.columns if k in by_key]
    subtotal, tax_amount, breakdown = _compute_tax(trips, invoice.tax_enabled, invoice.tax_mode, invoice.tax_rates)
    pdf_bytes = _build_pdf(invoice, invoice.client, invoice.company, trips, cols,
                           invoice.tax_enabled, invoice.tax_mode, subtotal, tax_amount, breakdown)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Invoice {invoice.invoice_no} - {invoice.client.name}.pdf"'
    return response


@login_required
def invoice_status(request):
    invoices = GeneratedInvoice.objects.select_related("client", "company").order_by("-created_at")
    return render(request, "operations/invoice_status.html", {
        "invoices": invoices,
        "status_choices": GeneratedInvoice.STATUS_CHOICES,
    })


@login_required
def invoice_status_update(request, invoice_id):
    invoice = get_object_or_404(GeneratedInvoice, pk=invoice_id)
    if request.method == "POST":
        status = request.POST.get("status")
        if status in dict(GeneratedInvoice.STATUS_CHOICES):
            invoice.status = status
            invoice.save(update_fields=["status"])
    return redirect("invoice_status")


def _build_pdf(invoice, client, company, trips, cols, tax_enabled, tax_mode, subtotal, tax_amount, breakdown):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=10 * mm, rightMargin=10 * mm,
                            topMargin=10 * mm, bottomMargin=10 * mm, title=f"Invoice - {client.name}")
    styles = getSampleStyleSheet()
    elements = [Paragraph("AL MURAD LOGISTICS", styles["Title"]), Spacer(1, 4 * mm)]

    # Service Recipient (the billed Company) / Service Provider (us), side by side.
    def party_block(title, name, address, ntn, stn):
        lines = [f"<b>{title}</b>", f"<font size=12><b>{name}</b></font>"]
        if address:
            lines.append(address.replace("\n", "<br/>"))
        if ntn:
            lines.append(f"<i>NTN No: {ntn}</i>")
        if stn:
            lines.append(f"<i>Tax Reg No: {stn}</i>")
        return Paragraph("<br/>".join(lines), styles["Normal"])

    header = Table([[
        party_block("Service Recipient Name", company.name, company.address, company.ntn, company.stn),
        party_block("Service Provider Name", "AL MURAD LOGISTICS", "", "", ""),
    ]], colWidths=[140 * mm, 137 * mm])
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8a8a8a")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (0, 0), 0.5, colors.HexColor("#9ca3af")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEAFTER", (0, 0), (0, -1), 0.5, colors.HexColor("#9ca3af")),
    ]))
    elements += [
        header, Spacer(1, 4 * mm),
        Paragraph(f"Invoice # <b>{invoice.invoice_no}</b> &bull; Client: <b>{client.name}</b> "
                  f"&bull; Generated on {date.today():%d-%b-%Y} &bull; {len(trips)} trip(s)", styles["Normal"]),
        Spacer(1, 6 * mm),
    ]

    trip_header = [label for _, label, _, _ in cols]
    money_cols = [i for i, (_, _, _, money) in enumerate(cols) if money]
    rows = [trip_header]
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
    elements.append(Spacer(1, 6 * mm))

    if tax_enabled and breakdown:
        tax_header = [f"Tax ({'Full' if tax_mode == 'FULL' else 'Partial'})", "Rate", "Taxable Amount", "Tax Amount"]
        tax_rows = [tax_header] + [
            [label, f"{rate:.2f}%", f"{base:,.0f}", f"{amount:,.0f}"] for label, rate, base, amount in breakdown
        ]
        tax_table = Table(tax_rows, colWidths=[60 * mm, 25 * mm, 45 * mm, 45 * mm])
        tax_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#374151")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#9ca3af")),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ]))
        elements += [tax_table, Spacer(1, 4 * mm)]

    summary_rows = [["Subtotal", f"{subtotal:,.0f}"]]
    if tax_enabled:
        summary_rows.append(["Tax", f"{tax_amount:,.0f}"])
    summary_rows.append(["GRAND TOTAL", f"{(subtotal + tax_amount):,.0f}"])
    summary = Table(summary_rows, colWidths=[40 * mm, 40 * mm], hAlign="RIGHT")
    summary.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9ca3af")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#fde68a")),
    ]))
    elements += [summary, Spacer(1, 14 * mm), Paragraph("____________________<br/>Authorized Signature", styles["Normal"])]
    doc.build(elements)
    return buffer.getvalue()
