"""Invoicing > Generate Invoice / Invoices Status.

Pick a client's trips over a date range, tick which ones to bill, choose (and
drag into order) the columns the Trip Details page should carry, optionally
work out sales tax, and download the Sales Tax Invoice as a PDF or an Excel
file - page 1 the invoice itself, page 2 the trip details. Every one
generated is logged as a GeneratedInvoice (client, company, trips, columns in
order, tax settings, totals) so Invoices Status can list them, track a status
on each, and rebuild the same invoice again on demand - the file itself is
never stored."""
import re
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from masters.models import DEFAULT_INVOICE_NOTES, Client, Company, TaxSettings
from . import invoice_pdf, invoice_xlsx
from .models import GeneratedInvoice, Trip

TRIP_RELATED = ("route__origin", "route__destination", "vehicle__vehicle_type", "vehicle_type",
                "sub_category", "stopover_city")

# (key, label, value-from-trip, is a money column that gets totalled)
COLUMNS = [
    ("trip_no", "Trip #", lambda t: t.trip_no, False),
    ("trip_date", "Date", lambda t: t.trip_date, False),
    ("bilty_number", "Bilty #", lambda t: t.bilty_number, False),
    ("vehicle", "Vehicle #", lambda t: t.vehicle.vehicle_number, False),
    ("vehicle_type", "Vehicle Type", lambda t: str(t.vehicle_type or t.vehicle.vehicle_type or ""), False),
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
DEFAULT_COLUMNS = ["trip_no", "trip_date", "bilty_number", "vehicle", "vehicle_type", "route", "weight",
                    "trip_charges", "additional_charges", "total_freight"]

# Full tax mode's jurisdictions (same keys as City.province) and the label
# each carries on the invoice, in the order the invoice lists them.
TAX_PROVINCES = [
    ("SINDH", "Sindh"), ("PUNJAB", "Punjab"), ("ICT", "ICT (Islamabad Capital Territory)"),
    ("KPK", "KPK (Khyber Pakhtoon Khuwa)"), ("BALOCHISTAN", "Balochistan"),
]

BLUE = "1F4E79"


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
    try:
        return Decimal(str(value or 0))
    except InvalidOperation:
        return Decimal(0)


def _pct(rate):
    return format(_d(rate).normalize(), "f") + "%"


def _parse_date(text):
    try:
        return date.fromisoformat(text) if text else None
    except ValueError:
        return None


@login_required
def invoice_select(request):
    client_id = request.GET.get("client") or ""
    start_date = request.GET.get("start_date") or ""
    end_date = request.GET.get("end_date") or ""
    client = Client.objects.filter(pk=client_id).first() if client_id else None
    trips = []
    if client:
        trips = Trip.objects.filter(client=client).select_related(*TRIP_RELATED)
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
    """Tax card fields: On/Off, Full/Partial and the 5 jurisdiction rate
    boxes (used by both modes). The boxes come pre-filled from the Tax menu
    but are editable per invoice, so what's typed here wins; a blank box falls
    back to the saved default. The rates that applied are returned as a
    snapshot to store on the invoice, so a redownload never changes if the Tax
    menu is edited later."""
    enabled = post.get("tax_enabled") == "on"
    mode = post.get("tax_mode") if post.get("tax_mode") in ("FULL", "PARTIAL") else ""
    if not enabled or not mode:
        return False, "", {}
    cfg = TaxSettings.current()

    def rate(field, default):
        raw = (post.get(field) or "").strip()
        if raw == "":
            return _d(default)
        return min(max(_d(raw), Decimal(0)), Decimal(100))

    rates = {code: rate(f"tax_{code.lower()}", getattr(cfg, f"{code.lower()}_percent")) for code, _ in TAX_PROVINCES}
    return True, mode, {k: str(v) for k, v in rates.items()}


def _compute_tax(trips, tax_enabled, tax_mode, tax_rates):
    """Returns (subtotal, tax_amount, breakdown) where breakdown is a list of
    (label, rate%, taxable base, tax amount) rows for the invoice's tax table.

    Full: each trip's whole amount is taxed at its route's ORIGIN city's
    jurisdiction rate. Partial: each trip is split 50/50 - the origin half at
    the origin city's jurisdiction rate, the destination half at the
    destination city's - worked out trip by trip, so one invoice can mix
    routes (e.g. ICT and Punjab). A city with no province set pays no tax."""
    subtotal = sum((_d(t.freight) for t in trips), Decimal(0))
    if not tax_enabled:
        return subtotal, Decimal(0), []

    rates = {k: _d(v) for k, v in tax_rates.items()}
    base_by_code = {code: Decimal(0) for code, _ in TAX_PROVINCES}
    unmapped = Decimal(0)
    for t in trips:
        amount = _d(t.freight)
        if tax_mode == "FULL":
            parts = [(t.route.origin.province, amount)]
        else:
            origin_half = (amount / 2).quantize(Decimal("0.01"))
            parts = [(t.route.origin.province, origin_half), (t.route.destination.province, amount - origin_half)]
        for province, part in parts:
            if province in base_by_code:
                base_by_code[province] += part
            else:
                unmapped += part

    breakdown, tax_amount = [], Decimal(0)
    for code, label in TAX_PROVINCES:
        base, rate = base_by_code[code], rates.get(code, Decimal(0))
        amount = (base * rate / 100).quantize(Decimal("0.01"))
        tax_amount += amount
        breakdown.append((label, rate, base, amount))
    if unmapped:
        breakdown.append(("No Province Set", Decimal(0), unmapped, Decimal(0)))
    return subtotal, tax_amount, breakdown


_ONES = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve",
         "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
_TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]


def _words_below_1000(n):
    parts = []
    if n >= 100:
        parts.append(f"{_ONES[n // 100]} Hundred")
        n %= 100
    if n >= 20:
        parts.append(_TENS[n // 10] + (f"-{_ONES[n % 10]}" if n % 10 else ""))
    elif n:
        parts.append(_ONES[n])
    return " ".join(parts)


def amount_in_words(amount):
    """'Four Hundred Seventy-Six Thousand Two Hundred Ninety-Eight Rupees Only.'
    for the whole-rupee amount printed on the invoice (thousand / million
    grouping, matching the digits shown next to it)."""
    n = int(_d(amount).quantize(Decimal("1"), rounding="ROUND_HALF_UP"))
    if n == 0:
        return "Zero Rupees Only."
    parts = []
    for size, name in ((10**9, "Billion"), (10**6, "Million"), (1000, "Thousand"), (1, "")):
        chunk, n = divmod(n, size)
        if chunk:
            parts.append(f"{_words_below_1000(chunk)} {name}".strip())
    return " ".join(parts) + " Rupees Only."


def _billing_period(start, end):
    # Kept short so it fits its cell on one line: 01-30 Sep 2026 / 26 Aug - 26 Sep 2026.
    if start.year == end.year and start.month == end.month:
        return f"{start:%d}–{end:%d %b %Y}"
    if start.year == end.year:
        return f"{start:%d %b} – {end:%d %b %Y}"
    return f"{start:%d %b %Y} – {end:%d %b %Y}"


def _invoice_data(invoice, trips, cols):
    """Everything both the PDF and the Excel need, worked out once."""
    cfg = TaxSettings.current()
    inv_date = invoice.created_at.astimezone(ZoneInfo("Asia/Karachi")).date()
    start = invoice.period_start or (min(t.trip_date for t in trips) if trips else inv_date)
    end = invoice.period_end or (max(t.trip_date for t in trips) if trips else inv_date)
    subtotal, tax_amount, breakdown = _compute_tax(trips, invoice.tax_enabled, invoice.tax_mode, invoice.tax_rates)

    money_idx = [i for i, c in enumerate(cols) if c[3]]
    rows, totals = [], [Decimal(0)] * len(cols)
    for t in trips:
        row = []
        for i, (_, _, fn, money) in enumerate(cols):
            value = fn(t)
            if money:
                value = _d(value)
                totals[i] += value
            row.append(value)
        rows.append(row)

    company = invoice.company
    return {
        "invoice_no": invoice.invoice_no,
        "invoice_date": inv_date,
        "due_date": inv_date + timedelta(days=invoice.payment_days),
        "payment_days": invoice.payment_days,
        "sales_tax_no": invoice.sales_tax_no,
        "period": _billing_period(start, end),
        "bill_to": {"name": company.name, "address": company.address, "ntn": company.ntn, "strn": company.stn},
        "provider": {"name": cfg.provider_name, "address": cfg.provider_address,
                     "ntn": cfg.provider_ntn, "strn": cfg.provider_strn},
        "in_words": amount_in_words(subtotal + tax_amount),
        "notes": [re.sub(r"^(\d+[.)]|[•*-])\s*", "", line.strip())
                  for line in (invoice.notes.strip() or DEFAULT_INVOICE_NOTES).splitlines() if line.strip()],
        "subtotal": subtotal, "tax_enabled": invoice.tax_enabled, "tax_mode": invoice.tax_mode,
        "tax_amount": tax_amount, "breakdown": breakdown, "grand_total": subtotal + tax_amount,
        "headers": [c[1] for c in cols], "money_idx": money_idx, "money": [c[3] for c in cols],
        "keys": [c[0] for c in cols], "rows": rows, "totals": totals,
    }


def _safe_filename(text):
    return re.sub(r"\s+", " ", re.sub(r"[^A-Za-z0-9 ._()#-]", "", text)).strip(" .") or "Invoice"


def _respond(invoice, trips, cols, fmt):
    data = _invoice_data(invoice, trips, cols)
    name = _safe_filename(f"Invoice {invoice.invoice_no} - {invoice.company.name}")
    if fmt == "xlsx":
        response = HttpResponse(
            invoice_xlsx.build(data),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="{name}.xlsx"'
    else:
        response = HttpResponse(invoice_pdf.build(data), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{name}.pdf"'
    return response


@login_required
def invoice_generate_pdf(request):
    """Creates the invoice record and returns it as a PDF (format=pdf, the
    default) or an Excel file (format=xlsx)."""
    if request.method != "POST":
        return redirect("invoice_select")

    client = get_object_or_404(Client, pk=request.POST.get("client"))
    company_id = request.POST.get("company") or ""
    company = Company.objects.filter(pk=company_id).first() if company_id.isdigit() else None
    trip_ids = request.POST.getlist("trip_ids")
    problem = ("Please choose a Service Recipient (add one under Invoicing > Add Company if the list is empty)."
               if not company else "Please tick at least one trip." if not trip_ids else "")
    if problem:
        messages.error(request, problem)
        back = {"client": client.pk, "start_date": request.POST.get("start_date") or "",
                "end_date": request.POST.get("end_date") or ""}
        return redirect(f"{reverse('invoice_select')}?{urlencode(back)}")
    by_key = {c[0]: c for c in _client_columns(client)}
    # The columns arrive in the order they were dragged into on the page.
    col_keys = []
    for k in request.POST.getlist("columns"):
        if k in by_key and k not in col_keys:
            col_keys.append(k)
    if not col_keys:
        col_keys = [k for k in DEFAULT_COLUMNS if k in by_key]
    cols = [by_key[k] for k in col_keys]

    trips = list(Trip.objects.filter(pk__in=trip_ids, client=client)
                 .select_related(*TRIP_RELATED).order_by("trip_date", "id"))

    tax_enabled, tax_mode, tax_rates = _tax_inputs(request.POST)
    subtotal, tax_amount, _ = _compute_tax(trips, tax_enabled, tax_mode, tax_rates)
    try:
        payment_days = min(max(int(request.POST.get("payment_days")), 0), 365)
    except (TypeError, ValueError):
        payment_days = TaxSettings.current().payment_terms_days

    invoice = GeneratedInvoice.objects.create(
        client=client, company=company, columns=col_keys,
        period_start=_parse_date(request.POST.get("start_date")),
        period_end=_parse_date(request.POST.get("end_date")), payment_days=payment_days,
        notes=(TaxSettings.current().invoice_notes if request.POST.get("notes_auto") == "on"
               else request.POST.get("notes") or "").strip(),
        sales_tax_no=(request.POST.get("sales_tax_no") or "").strip()[:40],
        tax_enabled=tax_enabled, tax_mode=tax_mode, tax_rates=tax_rates,
        subtotal=subtotal, tax_amount=tax_amount, grand_total=subtotal + tax_amount,
        created_by=request.user if request.user.is_authenticated else None,
    )
    invoice.trips.set(trips)
    return _respond(invoice, trips, cols, request.POST.get("format"))


@login_required
def invoice_redownload(request, invoice_id):
    invoice = get_object_or_404(GeneratedInvoice.objects.select_related("client", "company"), pk=invoice_id)
    trips = list(invoice.trips.select_related(*TRIP_RELATED).order_by("trip_date", "id"))
    by_key = {c[0]: c for c in _client_columns(invoice.client)}
    cols = [by_key[k] for k in invoice.columns if k in by_key]
    return _respond(invoice, trips, cols, request.GET.get("format"))


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


# ---------------------------------------------------------------- formatting
def _money2(value):
    return f"{value:,.2f}" if value else "-"


def _cell_text(value, money):
    if money:
        return _money2(value)
    if hasattr(value, "strftime"):
        return value.strftime("%d-%b-%y")
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    return str(value) if value not in (None, "") else ""
