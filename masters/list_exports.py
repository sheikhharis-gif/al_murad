"""Download Excel buttons on the Client Directory and Staff / Driver list."""
from datetime import date

from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from .models import Client, Staff, Vehicle

_thin = Side(style="thin", color="A6A6A6")
_border = Border(left=_thin, right=_thin, top=_thin, bottom=_thin)


def _sheet(title, columns, rows, filename):
    """columns: [(header, width)]; rows: lists of values. Returns the .xlsx download."""
    wb = Workbook()
    ws = wb.active
    ws.title = title
    for c, (header, width) in enumerate(columns, start=1):
        cell = ws.cell(row=1, column=c, value=header)
        cell.font, cell.fill, cell.border = Font(bold=True, color="FFFFFF"), PatternFill("solid", fgColor="1F4E78"), _border
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[cell.column_letter].width = width
    for r, row in enumerate(rows, start=2):
        for c, value in enumerate(row, start=1):
            cell = ws.cell(row=r, column=c, value=None if value in ("", None) else value)
            cell.border = _border
            if isinstance(value, date):
                cell.number_format = "d-mmm-yy"
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:{ws.cell(row=1, column=len(columns)).column_letter}{max(ws.max_row, 1)}"
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="{filename} {date.today():%Y-%m-%d}.xlsx"'
    wb.save(response)
    return response


def client_excel(request):
    clients = Client.objects.select_related("client_type").order_by("name")
    columns = [("#", 5), ("Company Name", 34), ("Type", 14), ("POC 1", 20), ("POC 1 Phone", 15), ("POC 1 Email", 26),
               ("POC 2", 20), ("POC 2 Phone", 15), ("POC 2 Email", 26), ("NTN #", 16), ("STN #", 18),
               ("Terms of Service", 18), ("Billing Period", 15), ("Billing Company", 30), ("Address", 40),
               ("Sub-Categories", 13), ("Stopover Charges", 13), ("Fuel Threshold %", 12), ("Status", 10)]
    rows = [[
        i, c.name, c.client_type.name if c.client_type_id else "", c.poc1_name, c.poc1_phone, c.poc1_email,
        c.poc2_name, c.poc2_phone, c.poc2_email, c.ntn or "", c.stn, c.term_of_service, c.billing_period,
        c.billing_company, c.address, "Yes" if c.has_sub_categories else "", "Yes" if c.has_stopover else "",
        float(c.fuel_revision_threshold) if c.fuel_revision_threshold is not None else None,
        "Active" if c.is_active else "Inactive",
    ] for i, c in enumerate(clients, start=1)]
    return _sheet("Clients", columns, rows, "Clients")


def staff_excel(request):
    vehicles = {}
    for v in Vehicle.objects.exclude(driver__isnull=True, driver2__isnull=True).only("vehicle_number", "driver_id", "driver2_id"):
        for sid in (v.driver_id, v.driver2_id):
            if sid:
                vehicles.setdefault(sid, []).append(v.vehicle_number)
    staff = Staff.objects.order_by("name")
    columns = [("#", 5), ("Employee ID", 13), ("Name", 24), ("Father Name", 22), ("Designation", 16),
               ("Vehicle(s)", 18), ("Mobile 1", 15), ("Mobile 2", 15), ("CNIC #", 17), ("CNIC Expiry", 12),
               ("License #", 16), ("License Category", 14), ("License Expiry", 12), ("Date of Birth", 12),
               ("Joining Date", 12), ("Salary", 12), ("Address", 40), ("Primary Contact", 20),
               ("Primary Contact #", 15), ("Secondary Contact", 20), ("Secondary Contact #", 15),
               ("Next of Kin", 20), ("Next of Kin #", 15), ("Relation", 12), ("Status", 10)]
    rows = [[
        i, s.employee_id, s.name, s.father_name, s.designation, ", ".join(vehicles.get(s.id, [])),
        s.mobile1, s.mobile2, s.cnic, s.cnic_expiry, s.license_number, s.license_category, s.license_expiry,
        s.date_of_birth, s.joining_date, float(s.salary) if s.salary is not None else None, s.address,
        s.reference1_name, s.reference1_mobile, s.reference2_name, s.reference2_mobile,
        s.next_of_kin_name, s.next_of_kin_mobile, s.next_of_kin_relation, "Active" if s.is_active else "Inactive",
    ] for i, s in enumerate(staff, start=1)]
    return _sheet("Staff", columns, rows, "Staff - Drivers")
