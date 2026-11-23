"""Reports > Operational MIS Data.

A whole-business report, separate from the Trips page: headline figures
(jobs, trips, fleet, revenue, expenses, fuel, maintenance, profit), breakdowns
by client / vehicle / route / expense head, and the full MIS data sheet - one
row per trip in the client's MIS column layout. Downloadable as Excel and PDF.
"""
import datetime as dt
import io
from collections import OrderedDict
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from masters.models import Client, MaintenanceJob, Staff, Vehicle, Vendor
from .models import GeneratedInvoice, Job, JobExpense, JobFuelEntry, Trip

MIS_HEADERS = [
    "JOB #", "Trip #", "Own/Rental", "Supplier", "Vehicle #", "Vehicle Type", "Rate Category", "Date", "Client", "Sub-Category", "Bilty #",
    "Weight (Tons)", "Route", "Stopover City", "Status", "Invoice #", "Trip Charges", "Stopover Charges",
    "Additional Charges", "Total Freight",
    "Departure Meter", "Arrival Meter", "Running KMs",
    "Reached Date & Time", "Departure Date & Time", "Arrival Date & Time",
    "Delivery Date & Time", "Actual Transit",
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

# Columns in MIS_HEADERS that hold money and get summed in the Total row: the
# trip-charge columns (right after Stopover City) and the expense block.
MONEY_COLS = (
    [MIS_HEADERS.index("Trip Charges"), MIS_HEADERS.index("Stopover Charges"),
     MIS_HEADERS.index("Additional Charges"), MIS_HEADERS.index("Total Freight")]
    + list(range(MIS_HEADERS.index("Toll Plaza"), MIS_HEADERS.index("Total") + 1))
)


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

    jobs = Job.objects.select_related("vehicle__vehicle_type", "vehicle__vendor", "rental_supplier").order_by("job_number")
    if start_date:
        jobs = jobs.filter(job_date__gte=start_date)
    if end_date:
        jobs = jobs.filter(job_date__lte=end_date)
    if vehicle_id:
        # a monthly rental job's vehicles are on its trips
        jobs = jobs.filter(Q(vehicle_id=vehicle_id) | Q(trips__vehicle_id=vehicle_id)).distinct()
    if status:
        jobs = jobs.filter(status=status)
    if client_id:
        jobs = jobs.filter(trips__client_id=client_id).distinct()
    jobs = list(jobs)
    job_ids = [j.job_number for j in jobs]

    trips = Trip.objects.filter(job_id__in=job_ids).select_related(
        "client", "route", "vehicle__vehicle_type", "vehicle__vendor", "vehicle_type", "rate_vehicle_type",
        "sub_category", "stopover_city"
    ).prefetch_related("extra_stopover_cities").order_by("job_id", "id")
    if client_id:
        trips = trips.filter(client_id=client_id)
    if vehicle_id:
        trips = trips.filter(vehicle_id=vehicle_id)
    trips = list(trips)
    invoiced = Trip.invoiced_ids()
    # Invoice # of each invoiced trip (its live, uncancelled invoice)
    invoice_no = dict(GeneratedInvoice.trips.through.objects.exclude(generatedinvoice__status="CANCELLED")
                      .filter(trip_id__in=[t.id for t in trips])
                      .values_list("trip_id", "generatedinvoice__invoice_no"))
    for t in trips:
        t._invoiced = t.id in invoiced

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
            supplier = job.rental_supplier if job.rental_pool else (vehicle.vendor if vehicle and vehicle.vendor_id else None)
            ownership = "RENTAL" if job.rental_pool or (vehicle and vehicle.vehicle_mode == "RENTAL") else "OWN"
            rate_category = _rate_category_label(t) if t else "Not Set"
            row = [
                job.job_code, t.trip_no if t else "", ownership, supplier.name if supplier else (vehicle.owner if vehicle and ownership == "RENTAL" else ""),
                vehicle.vehicle_number if vehicle else job.vehicle_label,
                str((t.vehicle_type if t else None) or (vehicle.vehicle_type if vehicle else "") or ""),
                rate_category,
                t.trip_date if t else job.job_date,
                (t.client.name if t.client_id else "Empty Trip") if t else "",
                (t.sub_category.name if t and t.sub_category_id else ""),
                t.bilty_number if t else "",
                t.weight if t else None, t.route.route_code if t else "",
                (t.stopover_names if t else ""),
                t.status_display if t else "",
                invoice_no.get(t.id, "") if t else "",
                (t.freight - (t.additional_charges or 0) - (t.stopover_charges or 0)) if t else None,
                t.stopover_charges if t else None,
                t.additional_charges if t else None,
                t.freight if t else None,
                # Meters / KMs are whole numbers - shown without decimals
                _whole(t.departure_meter) if t else None, _whole(t.arrival_meter) if t else None,
                _whole(t.arrival_meter - t.departure_meter)
                if t and t.arrival_meter is not None and t.departure_meter is not None else None,
                _local(t.reached_at) if t else None, _local(t.departed_at) if t else None,
                _local(t.arrived_at) if t else None, _local(t.delivered_at) if t else None,
                t.actual_transit_display if t else "",
            ]
            show_expense = idx == 0 and expense is not None
            # a monthly rental trip's own expenses go in their columns on its row
            own = {"fuel": t.trip_fuel, "weighbridge": t.trip_weighbridge, "loading": t.trip_loading,
                   "offloading": t.trip_offloading} if t else {}
            for field, _ in EXPENSE_FIELDS:
                value = getattr(expense, field) if show_expense else None
                if own.get(field):
                    value = (value or 0) + own[field]
                row.append(value)
            total = expense.total if show_expense else None
            if t and t.trip_expense_total:  # incl. the trip's hire fare
                total = (total or 0) + t.trip_expense_total
            row.append(total)
            row.append(t.remarks if t else (job.remarks or ""))
            rows.append(row)

    totals = [None] * len(MIS_HEADERS)
    totals[0] = "Total"
    for col in MONEY_COLS:
        totals[col] = sum((_d(r[col]) for r in rows), Decimal(0))
    km_col = MIS_HEADERS.index("Running KMs")
    totals[km_col] = sum((r[km_col] or 0 for r in rows), 0)

    # ---- Headline figures
    freight = sum((_d(t.freight) for t in trips), Decimal(0))
    additional = sum((_d(t.additional_charges) for t in trips), Decimal(0))
    trip_expense = sum((_d(e.total) for e in expenses.values()), Decimal(0)) + sum((_d(t.trip_expense_total) for t in trips), Decimal(0))
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
        ("Vehicles Used", len({t.vehicle_id for t in trips} | {j.vehicle_id for j in jobs if j.vehicle_id}), "int"),
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
        if not t.client_id:  # Empty Trip - nothing billed to any client
            continue
        c = by_client.setdefault(t.client.name, {"trips": 0, "weight": Decimal(0), "kms": Decimal(0), "freight": Decimal(0)})
        c["trips"] += 1
        c["weight"] += _d(t.weight)
        c["kms"] += _d(t.route.distance_km)
        c["freight"] += _d(t.freight)
    by_client = sorted(by_client.items(), key=lambda kv: -kv[1]["freight"])

    by_vehicle = OrderedDict()

    def vehicle_entry(key, vtype):
        return by_vehicle.setdefault(key, {
            "type": vtype, "jobs": 0, "trips": 0, "kms": Decimal(0),
            "freight": Decimal(0), "expense": Decimal(0), "liters": Decimal(0), "fuel": Decimal(0),
        })
    for job_id, job_trips in trips_by_job.items():
        job = job_by_id[job_id]
        if job.rental_pool:
            # each hired vehicle on its own line (freight - its hire fare), the
            # job's shared costs on the job's line
            for t in job_trips:
                v = vehicle_entry(t.vehicle.vehicle_number, str(t.vehicle_type or t.vehicle.vehicle_type or ""))
                v["trips"] += 1
                v["freight"] += _d(t.freight)
                v["expense"] += _d(t.trip_expense_total)
            v = vehicle_entry(job.vehicle_label, "RENTAL")
            v["jobs"] += 1
            v["expense"] += _d(expenses[job_id].total) if job_id in expenses else 0
            continue
        if not job.vehicle_id:
            # No fixed vehicle - each trip's own vehicle gets its own line (like a
            # rental job), the job's shared costs go on a line of their own.
            for t in job_trips:
                v = vehicle_entry(t.vehicle.vehicle_number, str(t.vehicle_type or t.vehicle.vehicle_type or ""))
                v["trips"] += 1
                v["kms"] += _d(t.route.distance_km)
                v["freight"] += _d(t.freight)
            v = vehicle_entry(f"Job #{job.job_code}", "MULTI-VEHICLE")
            v["jobs"] += 1
            v["expense"] += _d(expenses[job_id].total) if job_id in expenses else 0
            v["liters"] += _d(fuel_by_job.get(job_id, {}).get("liters"))
            v["fuel"] += _d(fuel_by_job.get(job_id, {}).get("amount"))
            continue
        v = vehicle_entry(job.vehicle.vehicle_number, str(job.vehicle.vehicle_type or ""))
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


def _rate_category_label(trip):
    weight = trip.rate_weight if trip.rate_weight is not None else trip.weight
    vehicle_type = trip.rate_vehicle_type if trip.rate_vehicle_type_id else trip.vehicle_type
    if not vehicle_type and trip.vehicle_id:
        vehicle_type = trip.vehicle.vehicle_type
    if weight is None or not vehicle_type:
        return "Empty Trip" if trip.empty_trip else "Not Set"
    prefix = "" if trip.rate_vehicle_type_id and trip.rate_weight is not None else "Default - "
    return f"{prefix}{weight.normalize():f} Ton - {vehicle_type.name}"


RENTAL_HEADERS = ["Job #", "Trip #", "Date", "Client", "Supplier", "Vehicle #", "Vehicle Type",
                  "Route", "Weight (Tons)", "Rate Category", "Complete Trip Fare", "Trip Expenses",
                  "Expense %", "Profit/Loss", "Profit/Loss %"]


def build_rental_mis(request):
    """Trip-wise income and cost report for rental vehicles only."""
    start_date = request.GET.get("start_date") or ""
    end_date = request.GET.get("end_date") or ""
    supplier_id = request.GET.get("supplier") or ""
    client_id = request.GET.get("client") or ""
    search = (request.GET.get("q") or "").strip()
    rental_jobs = Job.objects.filter(
        Q(rental_pool=True) | Q(vehicle__vehicle_mode="RENTAL") | Q(trips__vehicle__vehicle_mode="RENTAL")
    ).select_related("vehicle__vendor", "rental_supplier").distinct()
    if supplier_id.isdigit():
        rental_jobs = rental_jobs.filter(
            Q(rental_supplier_id=supplier_id) | Q(vehicle__vendor_id=supplier_id) | Q(trips__vehicle__vendor_id=supplier_id)
        ).distinct()
    job_ids = list(rental_jobs.values_list("job_number", flat=True))
    trips = Trip.objects.filter(job_id__in=job_ids).filter(
        Q(job__rental_pool=True) | Q(job__vehicle__vehicle_mode="RENTAL") | Q(vehicle__vehicle_mode="RENTAL")
    ).select_related("job__rental_supplier", "job__vehicle__vendor", "vehicle__vendor", "vehicle__vehicle_type",
                     "vehicle_type", "rate_vehicle_type", "client", "route", "sub_category").order_by("job_id", "trip_date", "id")
    if start_date:
        trips = trips.filter(trip_date__gte=start_date)
    if end_date:
        trips = trips.filter(trip_date__lte=end_date)
    if client_id.isdigit():
        trips = trips.filter(client_id=client_id)
    trips = list(trips)
    job_expenses = {e.job_id: e for e in JobExpense.objects.filter(job_id__in=job_ids)}
    fuel_by_job = {
        row["job_id"]: _d(row["amount"])
        for row in JobFuelEntry.objects.filter(job_id__in=job_ids).values("job_id").annotate(amount=Sum("amount"))
    }
    first_trip_by_job = {}
    for trip in trips:
        first_trip_by_job.setdefault(trip.job_id, trip.id)

    rows = []
    for trip in trips:
        job = trip.job
        vehicle = trip.vehicle
        supplier = job.rental_supplier or vehicle.vendor
        if not supplier and job.vehicle_id:
            supplier = job.vehicle.vendor
        if supplier_id.isdigit() and not (supplier and str(supplier.pk) == supplier_id):
            continue
        category = _rate_category_label(trip)
        shared = job_expenses.get(job.job_number)
        expense = _d(trip.trip_expense_total)
        if shared and first_trip_by_job.get(job.job_number) == trip.id:
            expense += _d(shared.total)
        if first_trip_by_job.get(job.job_number) == trip.id:
            expense += fuel_by_job.get(job.job_number, Decimal(0))
        fare = _d(trip.freight)
        profit = fare - expense
        expense_pct = expense / fare * 100 if fare else None
        profit_pct = profit / fare * 100 if fare else None
        values = [
            job.job_code, trip.trip_no, trip.trip_date, trip.client.name if trip.client_id else "Empty Trip",
            supplier.name if supplier else (vehicle.owner or ""), vehicle.vehicle_number,
            str(trip.vehicle_type or vehicle.vehicle_type or ""), trip.route.route_code,
            trip.weight, category, fare, expense, expense_pct, profit, profit_pct,
        ]
        rows.append({
            "trip_id": trip.pk, "trip_no": trip.trip_no, "values": values,
            "missing_expense": expense == 0, "is_loss": profit < 0,
            "expense_fields": {
                "trip_fare": trip.trip_fare, "trip_fuel": trip.trip_fuel,
                "trip_weighbridge": trip.trip_weighbridge, "trip_loading": trip.trip_loading,
                "trip_offloading": trip.trip_offloading,
            },
        })
    if search:
        needle = search.casefold()
        rows = [row for row in rows if any(needle in str(value).casefold() for value in row["values"] if value is not None)]
    total_fare = sum((_d(row["values"][10]) for row in rows), Decimal(0))
    total_expenses = sum((_d(row["values"][11]) for row in rows), Decimal(0))
    total_profit = total_fare - total_expenses
    totals = ["Total", "", "", "", "", "", "", "", "", "", total_fare, total_expenses,
              total_expenses / total_fare * 100 if total_fare else None, total_profit,
              total_profit / total_fare * 100 if total_fare else None]
    return {
        "headers": RENTAL_HEADERS, "rows": rows, "totals": totals,
        "start_date": start_date, "end_date": end_date, "supplier_id": supplier_id,
        "client_id": client_id, "search": search,
        "clients": Client.objects.filter(trips__job__in=rental_jobs).distinct().order_by("name"),
        "suppliers": Vendor.objects.filter(Q(rental_jobs__isnull=False) | Q(vehicles__vehicle_mode="RENTAL")).distinct().order_by("name"),
        "query": request.GET.urlencode(), "trip_count": len(rows),
        "total_fare": total_fare, "total_expenses": total_expenses, "profit_loss": total_profit,
        "total_expense_pct": total_expenses / total_fare * 100 if total_fare else None,
        "profit_pct": total_profit / total_fare * 100 if total_fare else None,
    }


@login_required
def rental_mis_report(request):
    return render(request, "operations/rental_mis_report.html", build_rental_mis(request))


@login_required
def rental_mis_excel(request):
    data = build_rental_mis(request)
    wb = Workbook()
    ws = wb.active
    ws.title = "Rental MIS"
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="1F4E79")
    border = Border(bottom=Side(style="thin", color="D9E2F3"))
    ws.append(["Al Murad Logistics - Rental MIS"])
    ws["A1"].font = Font(bold=True, size=14)
    ws.append(data["headers"])
    for cell in ws[2]:
        cell.font, cell.fill = header_font, header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for row in data["rows"]:
        ws.append(row["values"])
    ws.append(data["totals"])
    for row in ws.iter_rows(min_row=3):
        for cell in row:
            cell.border = border
            if isinstance(cell.value, Decimal):
                cell.value = float(cell.value)
                cell.number_format = "#,##0.00"
            elif isinstance(cell.value, dt.date):
                cell.number_format = "dd-mmm-yy"
        for col in (13, 15):
            ws.cell(row=row[0].row, column=col).number_format = '0.00"%"'
    for cell in ws[ws.max_row]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="D9E2F3")
    widths = [12, 12, 14, 26, 26, 16, 18, 14, 14, 24, 22, 18, 14, 18, 16]
    for idx, width in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(idx)].width = width
    ws.freeze_panes = "A3"
    ws.auto_filter.ref = f"A2:{get_column_letter(len(data['headers']))}{max(ws.max_row - 1, 2)}"
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="Rental MIS.xlsx"'
    wb.save(response)
    return response


@login_required
@require_POST
def rental_trip_expense_update(request, trip_id):
    rental_trips = Trip.objects.filter(
        Q(job__rental_pool=True) | Q(job__vehicle__vehicle_mode="RENTAL") | Q(vehicle__vehicle_mode="RENTAL")
    )
    trip = get_object_or_404(rental_trips, pk=trip_id)
    fields = ("trip_fare", "trip_fuel", "trip_weighbridge", "trip_loading", "trip_offloading")
    values = {}
    maximum = Decimal("9999999999.99")
    try:
        for field in fields:
            raw = (request.POST.get(field) or "0").strip().replace(",", "")
            value = Decimal(raw).quantize(Decimal("0.01"))
            if not value.is_finite() or value < 0 or value > maximum:
                raise InvalidOperation
            values[field] = value
    except (InvalidOperation, ValueError):
        messages.error(request, "Expense values must be valid non-negative amounts.")
    else:
        Trip.objects.filter(pk=trip.pk).update(**values)
        messages.success(request, f"Expenses saved for Trip #{trip.trip_no}.")
    query = request.META.get("QUERY_STRING", "")
    return redirect(f"{reverse('rental_mis_report')}?{query}" if query else "rental_mis_report")


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
    widths = {"Client": 28, "Supplier": 25, "Route": 12, "Remarks": 30, "Vehicle #": 13,
              "Vehicle Type": 14, "Rate Category": 20, "Own/Rental": 13,
              "Actual Transit": 16, "Invoice #": 20}
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
