"""Reports > Operational MIS Data.

A whole-business report, separate from the Trips page: headline figures
(jobs, trips, fleet, revenue, expenses, fuel, maintenance, profit), breakdowns
by client / vehicle / route / expense head, and the full MIS data sheet - one
row per trip in the client's MIS column layout. Downloadable as Excel and PDF.
"""
import datetime as dt
import io
from collections import OrderedDict
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from masters.models import Client, MaintenanceJob, Staff, Vehicle
from .models import Job, JobExpense, JobFuelEntry, Trip

MIS_HEADERS = [
    "JOB #", "Trip #", "Vehicle #", "Vehicle Type", "Date", "Client", "Bilty #",
    "Weight (Tons)", "Route", "Status", "Departure Meter", "Arrival Meter", "Running KMs",
    "Reached Date & Time", "Departure Date & Time", "Arrival Date & Time",
    "Delivery Date & Time", "Actual Transit", "Trip Charges", "Additional Charges",
    "Toll Plaza", "Food", "Incentive", "Mobile Expense", "Challan", "Tyre Expense",
    "Service", "Loading", "Offloading", "Weighbridge", "Maintenance",
    "Labor Charges", "Fuel", "Other", "Total", "Remarks",
]

EXPENSE_FIELDS = [
    ("toll_plaza", "Toll Plaza"), ("food", "Food"), ("incentive", "Incentive"),
    ("mobile_expense", "Mobile Expense"), ("challan", "Challan"),
    ("tyre_expense", "Tyre Expense"), ("service", "Service"), ("loading", "Loading"),
    ("offloading", "Offloading"), ("weighbridge", "Weighbridge"),
    ("maintenance", "Maintenance"), ("labor_charges", "Labor Charges"),
    ("fuel", "Fuel"), ("other", "Other"),
]

# Columns in MIS_HEADERS that hold money and get summed in the Total row
MONEY_START = MIS_HEADERS.index("Trip Charges")
MONEY_END = MIS_HEADERS.index("Total")


def _d(value):
    return Decimal(str(value or 0))


def _whole(value):
    return int(round(value)) if value is not None else None


def _local(value):
    return timezone.localtime(value).replace(tzinfo=None, microsecond=0) if value else None


def build_mis(request):
    """All MIS figures for the filters in request.GET (date range on job date,
    client, vehicle, job status)."""
    start_date = request.GET.get("start_date") or ""
    end_date = request.GET.get("end_date") or ""
    client_id = request.GET.get("client") or ""
    vehicle_id = request.GET.get("vehicle") or ""
    status = request.GET.get("status") or ""

    jobs = Job.objects.select_related("vehicle__vehicle_type").order_by("job_number")
    if start_date:
        jobs = jobs.filter(job_date__gte=start_date)
    if end_date:
        jobs = jobs.filter(job_date__lte=end_date)
    if vehicle_id:
        jobs = jobs.filter(vehicle_id=vehicle_id)
    if status:
        jobs = jobs.filter(status=status)
    if client_id:
        jobs = jobs.filter(trips__client_id=client_id).distinct()
    jobs = list(jobs)
    job_ids = [j.job_number for j in jobs]

    trips = Trip.objects.filter(job_id__in=job_ids).select_related(
        "client", "route", "vehicle__vehicle_type", "vehicle_type"
    ).order_by("job_id", "id")
    if client_id:
        trips = trips.filter(client_id=client_id)
    trips = list(trips)

    expenses = {e.job_id: e for e in JobExpense.objects.filter(job_id__in=job_ids)}
    fuel_by_job = {
        r["job_id"]: r for r in JobFuelEntry.objects.filter(job_id__in=job_ids)
        .values("job_id").annotate(liters=Sum("liters"), amount=Sum("amount"))
    }

    trips_by_job = OrderedDict((j.job_number, []) for j in jobs)
    for t in trips:
        trips_by_job[t.job_id].append(t)
    job_by_id = {j.job_number: j for j in jobs}

    # ---- MIS data rows: one per trip; a job's shared expense breakdown goes on
    # its first trip row only (so the totals don't double-count it). A job with
    # no trips yet still gets a row so its expenses aren't lost.
    rows = []
    for job_id, job_trips in trips_by_job.items():
        job = job_by_id[job_id]
        expense = expenses.get(job_id)
        for idx, t in enumerate(job_trips or [None]):
            vehicle = t.vehicle if t else job.vehicle
            row = [
                job.job_code, t.trip_no if t else "", vehicle.vehicle_number,
                str((t.vehicle_type if t else None) or vehicle.vehicle_type or ""),
                t.trip_date if t else job.job_date,
                t.client.name if t else "", t.bilty_number if t else "",
                t.weight if t else None, t.route.route_code if t else "",
                t.status_display if t else "",
                # Meters / KMs are whole numbers - shown without decimals
                _whole(t.departure_meter) if t else None, _whole(t.arrival_meter) if t else None,
                _whole(t.arrival_meter - t.departure_meter)
                if t and t.arrival_meter is not None and t.departure_meter is not None else None,
                _local(t.reached_at) if t else None, _local(t.departed_at) if t else None,
                _local(t.arrived_at) if t else None, _local(t.delivered_at) if t else None,
                t.actual_transit_display if t else "",
                (t.freight - (t.additional_charges or 0)) if t else None,
                t.additional_charges if t else None,
            ]
            show_expense = idx == 0 and expense is not None
            for field, _ in EXPENSE_FIELDS:
                row.append(getattr(expense, field) if show_expense else None)
            row.append(expense.total if show_expense else None)
            row.append(t.remarks if t else (job.remarks or ""))
            rows.append(row)

    totals = [None] * len(MIS_HEADERS)
    totals[0] = "Total"
    for col in range(MONEY_START, MONEY_END + 1):
        totals[col] = sum((_d(r[col]) for r in rows), Decimal(0))
    km_col = MIS_HEADERS.index("Running KMs")
    totals[km_col] = sum((r[km_col] or 0 for r in rows), 0)

    # ---- Headline figures
    freight = sum((_d(t.freight) for t in trips), Decimal(0))
    additional = sum((_d(t.additional_charges) for t in trips), Decimal(0))
    trip_expense = sum((_d(e.total) for e in expenses.values()), Decimal(0))
    fuel_liters = sum((_d(f["liters"]) for f in fuel_by_job.values()), Decimal(0))
    fuel_amount = sum((_d(f["amount"]) for f in fuel_by_job.values()), Decimal(0))
    running_kms = totals[km_col]
    net_profit = freight - trip_expense - fuel_amount

    maintenance = MaintenanceJob.objects.all()
    if start_date:
        maintenance = maintenance.filter(date__gte=start_date)
    if end_date:
        maintenance = maintenance.filter(date__lte=end_date)
    if vehicle_id:
        maintenance = maintenance.filter(vehicle_id=vehicle_id)
    maintenance_cost = _d(maintenance.aggregate(t=Sum("total_cost"))["t"])

    status_labels = dict(Job.STATUS_CHOICES)
    status_counts = OrderedDict((label, 0) for label in status_labels.values())
    for j in jobs:
        status_counts[status_labels.get(j.status, j.status)] += 1

    summary = [
        ("Total Jobs", len(jobs), "int"),
        ("Total Trips", len(trips), "int"),
        ("Vehicles Used", len({j.vehicle_id for j in jobs}), "int"),
        ("Clients Served", len({t.client_id for t in trips}), "int"),
        ("Running KMs", running_kms, "int"),
        ("Freight Revenue", freight, "money"),
        ("Additional Charges", additional, "money"),
        ("Trip Advance Given", sum((_d(j.trip_advance) for j in jobs), Decimal(0)), "money"),
        ("Trip Expenses", trip_expense, "money"),
        ("Fuel Filled (Liters)", fuel_liters, "num"),
        ("Fuel Expense", fuel_amount, "money"),
        ("Net Profit (Freight - Trip Exp - Fuel)", net_profit, "money"),
        ("Profit %", round(net_profit / freight * 100, 2) if freight else Decimal(0), "pct"),
        ("Cost per KM", round((trip_expense + fuel_amount) / running_kms, 2) if running_kms else Decimal(0), "money"),
        ("Fuel Average (KM / Liter)", round(running_kms / fuel_liters, 2) if fuel_liters else Decimal(0), "num"),
        ("Workshop Maintenance Cost", maintenance_cost, "money"),
    ]

    fleet = [
        ("Total Vehicles", Vehicle.objects.count()),
        ("Own Vehicles", Vehicle.objects.filter(vehicle_mode="OWN").count()),
        ("Rental Vehicles", Vehicle.objects.exclude(vehicle_mode="OWN").count()),
        ("Active Clients", Client.objects.filter(is_active=True).count()),
        ("Active Staff", Staff.objects.filter(is_active=True).count()),
        ("Maintenance Jobs (period)", maintenance.count()),
    ] + [(f"Jobs - {label}", count) for label, count in status_counts.items()]

    # ---- Breakdowns
    by_client = OrderedDict()
    for t in trips:
        c = by_client.setdefault(t.client.name, {"trips": 0, "weight": Decimal(0), "kms": Decimal(0), "freight": Decimal(0)})
        c["trips"] += 1
        c["weight"] += _d(t.weight)
        c["kms"] += _d(t.route.distance_km)
        c["freight"] += _d(t.freight)
    by_client = sorted(by_client.items(), key=lambda kv: -kv[1]["freight"])

    by_vehicle = OrderedDict()
    for job_id, job_trips in trips_by_job.items():
        job = job_by_id[job_id]
        v = by_vehicle.setdefault(job.vehicle.vehicle_number, {
            "type": str(job.vehicle.vehicle_type or ""), "jobs": 0, "trips": 0, "kms": Decimal(0),
            "freight": Decimal(0), "expense": Decimal(0), "liters": Decimal(0), "fuel": Decimal(0),
        })
        v["jobs"] += 1
        v["trips"] += len(job_trips)
        v["kms"] += sum((_d(t.route.distance_km) for t in job_trips), Decimal(0))
        v["freight"] += sum((_d(t.freight) for t in job_trips), Decimal(0))
        v["expense"] += _d(expenses[job_id].total) if job_id in expenses else 0
        v["liters"] += _d(fuel_by_job.get(job_id, {}).get("liters"))
        v["fuel"] += _d(fuel_by_job.get(job_id, {}).get("amount"))
    for v in by_vehicle.values():
        v["profit"] = v["freight"] - v["expense"] - v["fuel"]
    by_vehicle = sorted(by_vehicle.items(), key=lambda kv: -kv[1]["freight"])

    by_route = OrderedDict()
    for t in trips:
        r = by_route.setdefault(t.route.route_code, {"trips": 0, "kms": _d(t.route.distance_km), "freight": Decimal(0)})
        r["trips"] += 1
        r["freight"] += _d(t.freight)
    by_route = sorted(by_route.items(), key=lambda kv: -kv[1]["trips"])

    expense_heads = []
    for field, label in EXPENSE_FIELDS:
        amount = sum((_d(getattr(e, field)) for e in expenses.values()), Decimal(0))
        expense_heads.append((label, amount, round(amount / trip_expense * 100, 1) if trip_expense else 0))

    return {
        "filters": {"start_date": start_date, "end_date": end_date, "client": client_id,
                    "vehicle": vehicle_id, "status": status},
        "summary": summary, "fleet": fleet,
        "by_client": by_client, "by_vehicle": by_vehicle, "by_route": by_route,
        "expense_heads": expense_heads, "trip_expense": trip_expense,
        "headers": MIS_HEADERS, "rows": rows, "totals": totals,
        # Same rows as display text for the web page (dates, 2-decimal money...)
        "display_rows": [[_fmt(v) for v in row] for row in rows],
        "display_totals": [_fmt(v) for v in totals],
    }


def _period_label(f):
    if f["start_date"] or f["end_date"]:
        return f"Period: {f['start_date'] or 'start'} to {f['end_date'] or 'today'}"
    return "Period: All records"


def _fmt(value):
    """Plain-text rendering for PDF cells."""
    if value is None:
        return ""
    if isinstance(value, dt.datetime):
        return value.strftime("%d-%b-%y %H:%M")
    if isinstance(value, dt.date):
        return value.strftime("%d-%b-%y")
    if isinstance(value, Decimal):
        return f"{value:,.2f}"
    return str(value)


@login_required
def mis_report(request):
    data = build_mis(request)
    data.update({
        "clients": Client.objects.order_by("name"),
        "vehicles": Vehicle.objects.order_by("vehicle_number"),
        "status_choices": Job.STATUS_CHOICES,
        "query": request.GET.urlencode(),
        "period_label": _period_label(data["filters"]),
    })
    return render(request, "operations/mis_report.html", data)


@login_required
def mis_excel(request):
    data = build_mis(request)
    wb = Workbook()

    bold = Font(bold=True, name="Segoe UI", size=9)
    normal = Font(name="Segoe UI", size=9)
    head_fill = PatternFill("solid", fgColor="D9D9D9")
    thin = Side(style="thin", color="A6A6A6")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    def write_row(ws, r, values, font=normal, fill=None):
        for c, value in enumerate(values, start=1):
            if isinstance(value, Decimal):
                value = float(value)
            cell = ws.cell(row=r, column=c, value=value)
            cell.font = font
            cell.border = border
            if fill:
                cell.fill = fill
            if isinstance(value, dt.datetime):
                cell.number_format = "dd-mmm-yy hh:mm"
            elif isinstance(value, dt.date):
                cell.number_format = "dd-mmm-yy"
            elif isinstance(value, float):
                cell.number_format = "#,##0.00"

    # Sheet 1: MIS data in the client's layout (header row 2, data from row 3)
    ws = wb.active
    ws.title = "MIS Data"
    ws.cell(row=1, column=1, value=f"Al Murad Logistics - Operational MIS Data ({_period_label(data['filters'])})").font = Font(bold=True, size=11)
    write_row(ws, 2, data["headers"], font=bold, fill=head_fill)
    for c in range(1, len(data["headers"]) + 1):
        ws.cell(row=2, column=c).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    r = 3
    for row in data["rows"]:
        write_row(ws, r, row)
        r += 1
    write_row(ws, r, data["totals"], font=bold, fill=head_fill)
    widths = {"Client": 28, "Route": 12, "Remarks": 30, "Vehicle #": 13, "Vehicle Type": 14, "Actual Transit": 16}
    for c, title in enumerate(data["headers"], start=1):
        ws.column_dimensions[get_column_letter(c)].width = widths.get(title, 18 if "Date & Time" in title else 12)
    ws.row_dimensions[2].height = 30
    ws.freeze_panes = "A3"
    ws.auto_filter.ref = f"A2:{get_column_letter(len(data['headers']))}{max(r - 1, 2)}"

    # Sheet 2: summary and breakdowns
    ss = wb.create_sheet("Summary")
    ss.cell(row=1, column=1, value="Al Murad Logistics - Operational MIS Summary").font = Font(bold=True, size=12)
    ss.cell(row=2, column=1, value=_period_label(data["filters"])).font = normal
    r = 4

    def section(title, header, rows):
        nonlocal r
        ss.cell(row=r, column=1, value=title).font = Font(bold=True, size=11)
        r += 1
        write_row(ss, r, header, font=bold, fill=head_fill)
        r += 1
        for row in rows:
            write_row(ss, r, row)
            r += 1
        r += 1

    section("Key Figures", ["Metric", "Value"], [(k, v) for k, v, _ in data["summary"]])
    section("Fleet & Operations", ["Item", "Count"], data["fleet"])
    section("Client-wise", ["Client", "Trips", "Weight (Tons)", "KMs", "Freight"],
            [(k, v["trips"], v["weight"], v["kms"], v["freight"]) for k, v in data["by_client"]])
    section("Vehicle-wise", ["Vehicle #", "Type", "Jobs", "Trips", "KMs", "Freight", "Trip Expense", "Fuel (L)", "Fuel Cost", "Profit"],
            [(k, v["type"], v["jobs"], v["trips"], v["kms"], v["freight"], v["expense"], v["liters"], v["fuel"], v["profit"]) for k, v in data["by_vehicle"]])
    section("Route-wise", ["Route", "KMs", "Trips", "Freight"],
            [(k, v["kms"], v["trips"], v["freight"]) for k, v in data["by_route"]])
    section("Expense Heads", ["Expense", "Amount", "% of Trip Expense"],
            [(label, amount, pct) for label, amount, pct in data["expense_heads"]])
    ss.column_dimensions["A"].width = 38
    for c in range(2, 11):
        ss.column_dimensions[get_column_letter(c)].width = 15

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="Operational MIS Data.xlsx"'
    wb.save(response)
    return response


@login_required
def mis_pdf(request):
    data = build_mis(request)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A3), leftMargin=8 * mm, rightMargin=8 * mm,
                            topMargin=10 * mm, bottomMargin=10 * mm, title="Operational MIS Data")
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("Al Murad Logistics - Operational MIS Data", styles["Title"]),
        Paragraph(_period_label(data["filters"]), styles["Normal"]),
        Spacer(1, 6 * mm),
    ]

    def table(rows, col_widths=None, font_size=8, total_row=False):
        t = Table([[_fmt(v) for v in row] for row in rows], colWidths=col_widths, repeatRows=1)
        style = [
            ("FONTSIZE", (0, 0), (-1, -1), font_size),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#9ca3af")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
        ]
        if total_row:
            style += [("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                      ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#d1d5db"))]
        t.setStyle(TableStyle(style))
        return t

    def heading(text):
        elements.append(Paragraph(text, styles["Heading2"]))

    key_rows = [["Metric", "Value"]] + [[k, v] for k, v, _ in data["summary"]]
    fleet_rows = [["Item", "Count"]] + [list(x) for x in data["fleet"]]
    side = Table([[table(key_rows, [80 * mm, 45 * mm], 9), table(fleet_rows, [80 * mm, 30 * mm], 9)]],
                 colWidths=[135 * mm, 120 * mm])
    side.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    heading("Key Figures / Fleet & Operations")
    elements.append(side)

    heading("Client-wise")
    elements.append(table([["Client", "Trips", "Weight (Tons)", "KMs", "Freight"]] +
                          [[k, v["trips"], v["weight"], v["kms"], v["freight"]] for k, v in data["by_client"]]))
    heading("Vehicle-wise")
    elements.append(table([["Vehicle #", "Type", "Jobs", "Trips", "KMs", "Freight", "Trip Expense", "Fuel (L)", "Fuel Cost", "Profit"]] +
                          [[k, v["type"], v["jobs"], v["trips"], v["kms"], v["freight"], v["expense"], v["liters"], v["fuel"], v["profit"]]
                           for k, v in data["by_vehicle"]]))
    heading("Route-wise")
    elements.append(table([["Route", "KMs", "Trips", "Freight"]] +
                          [[k, v["kms"], v["trips"], v["freight"]] for k, v in data["by_route"]]))
    heading("Expense Heads")
    elements.append(table([["Expense", "Amount", "% of Trip Expense"]] +
                          [[label, amount, f"{pct}%"] for label, amount, pct in data["expense_heads"]]))

    # Full MIS data sheet - 35 columns, so small type on its own page(s)
    elements += [PageBreak()]
    heading("MIS Data (one row per trip)")
    detail = [data["headers"]] + data["rows"] + [data["totals"]]
    detail = [[Paragraph(f"<font size=4.6>{_fmt(v)}</font>", styles["BodyText"]) for v in row] for row in detail]
    detail_table = Table(detail, repeatRows=1, colWidths=[(420 - 16) / len(data["headers"]) * mm] * len(data["headers"]))
    detail_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d9d9d9")),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#d9d9d9")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#9ca3af")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 1), ("RIGHTPADDING", (0, 0), (-1, -1), 1),
        ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    elements.append(detail_table)

    doc.build(elements)
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="Operational MIS Data.pdf"'
    return response
