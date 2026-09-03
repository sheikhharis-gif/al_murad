import json
from calendar import monthrange
from urllib.parse import urlencode
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db.models import Sum, Count
from django.db.models.deletion import ProtectedError
from datetime import date

from .models import (
    Staff, Vehicle, VehicleType, Wheeler, City, Route,
    Vendor, SupplierType, Client, Expense, VehicleTyre,
    ClientRate, DriverSalary,
    StaffMonthlyAccount, StaffAttendanceEntry, StaffAccountEntry,
    FuelProduct, VendorFuelPrice,
)

from .forms import (
    StaffForm, VehicleForm, VehicleTyreForm, VehiclePermitsForm,
    VehicleTypeForm, WheelerForm,
    CityForm, RouteForm,
    VendorForm, SupplierTypeForm, ClientForm,
    ExpenseForm, ClientRateForm,
    DriverSalaryForm,
    StaffAttendanceFormSet, StaffAccountEntryFormSet,
    FuelProductForm, VendorFuelPriceFormSet,
)


def _sorted_queryset(request, queryset, sort_fields, default_sort, default_order="asc"):
    sort_by = request.GET.get("sort_by", default_sort)
    order = request.GET.get("order", default_order)
    if sort_by not in sort_fields:
        sort_by = default_sort
    if order not in ("asc", "desc"):
        order = default_order
    order_field = sort_by if order == "asc" else f"-{sort_by}"
    return queryset.order_by(order_field), sort_by, order


# ================= STAFF =================
STAFF_SORT_FIELDS = {
    "name": "Full Name",
    "employee_id": "Employee ID",
    "designation": "Designation",
    "mobile1": "Mobile Number",
    "cnic": "CNIC",
    "joining_date": "Joining Date",
    "is_active": "Status",
}

def staff_list(request):
    staff, sort_by, order = _sorted_queryset(
        request, Staff.objects.all(), STAFF_SORT_FIELDS, "name"
    )
    return render(request, "staff/staff_list.html", {
        "staff": staff,
        "sort_fields": STAFF_SORT_FIELDS,
        "sort_by": sort_by,
        "order": order,
    })


def staff_add(request):
    form = StaffForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("staff_list")
    return render(request, "staff/staff_form.html", {"form": form})
# ================= STAFF EDIT & DELETE =================

def staff_edit(request, staff_id):
    staff_member = get_object_or_404(Staff, id=staff_id)
    if request.method == "POST":
        form = StaffForm(request.POST, instance=staff_member)
        if form.is_valid():
            form.save()
            return redirect("staff_list")
    else:
        form = StaffForm(instance=staff_member)
    return render(request, "staff/staff_form.html", {"form": form, "staff": staff_member})

def staff_delete(request, staff_id):
    staff_member = get_object_or_404(Staff, id=staff_id)
    staff_member.delete()
    return redirect("staff_list")


# ================= STAFF MONTHLY ACCOUNT & EXPENSE STATEMENT =================
def staff_account_select(request):
    staff = Staff.objects.filter(is_active=True).order_by("name")
    return render(request, "staff/staff_account_select.html", {"staff": staff})


def staff_account(request, staff_id):
    staff_member = get_object_or_404(Staff, id=staff_id)

    month_param = request.GET.get("month")
    try:
        requested_month = date(int(month_param[:4]), int(month_param[5:7]), 1) if month_param else date.today().replace(day=1)
    except (ValueError, IndexError):
        requested_month = date.today().replace(day=1)

    # Reporting month can't move forward until the currently open month for
    # this staff member is closed - snap back to it if a different month was requested.
    active = StaffMonthlyAccount.objects.filter(staff=staff_member, is_closed=False).order_by("-month").first()
    if active and active.month != requested_month:
        messages.warning(
            request,
            f"{active.month:%B %Y} ka account abhi close nahi hua - pehle usay close karen, phir naya reporting month khulega."
        )
        requested_month = active.month

    account, created = StaffMonthlyAccount.objects.get_or_create(staff=staff_member, month=requested_month)
    if created:
        previous = StaffMonthlyAccount.objects.filter(
            staff=staff_member, month__lt=requested_month
        ).order_by("-month").first()
        if previous:
            account.opening_balance = previous.closing_balance
            account.save()

        days_in_month = monthrange(requested_month.year, requested_month.month)[1]
        StaffAttendanceEntry.objects.bulk_create([
            StaffAttendanceEntry(account=account, date=requested_month.replace(day=d))
            for d in range(1, days_in_month + 1)
        ])

    redirect_url = f"{reverse('staff_account', args=[staff_member.id])}?month={account.month:%Y-%m}"

    if request.method == "POST":
        if account.is_closed:
            messages.error(request, "Ye month band ho chuka hai - ab isay edit nahi kiya ja sakta.")
            return redirect(redirect_url)

        if "save_attendance" in request.POST:
            attendance_formset = StaffAttendanceFormSet(request.POST, queryset=account.attendance.all(), prefix="att")
            if attendance_formset.is_valid():
                attendance_formset.save()
                messages.success(request, "Attendance sheet updated successfully.")
            else:
                messages.error(request, "Attendance mein kuch masla hai - dobara check karen.")
            return redirect(redirect_url)

        if "save_account" in request.POST:
            account_formset = StaffAccountEntryFormSet(request.POST, queryset=account.entries.all(), prefix="acc")
            if account_formset.is_valid():
                entries = account_formset.save(commit=False)
                for entry in entries:
                    entry.account = account
                    entry.save()
                for obj in account_formset.deleted_objects:
                    obj.delete()
                messages.success(request, "Staff account updated successfully.")
            else:
                messages.error(request, "Staff account mein kuch masla hai - dobara check karen.")
            return redirect(redirect_url)

        if "close_month" in request.POST:
            account.is_closed = True
            account.closed_date = date.today()
            account.save()
            messages.success(request, f"{account.month:%B %Y} ka account close ho gaya. Ab Payslip generate ki ja sakti hai.")
            return redirect(redirect_url)

    attendance_formset = StaffAttendanceFormSet(queryset=account.attendance.all(), prefix="att")
    account_formset = StaffAccountEntryFormSet(queryset=account.entries.all(), prefix="acc")

    if account.is_closed:
        for f in list(attendance_formset) + list(account_formset):
            for field in f.fields.values():
                field.widget.attrs["disabled"] = True

    running = account.opening_balance or 0
    account_rows = []
    for form in account_formset:
        entry = form.instance
        if entry.pk:
            running = running + (entry.amount or 0) - (entry.paid or 0) - (entry.expense or 0)
            account_rows.append((form, running))
        else:
            account_rows.append((form, None))

    payslip_params = urlencode({
        "staff": staff_member.id,
        "month": f"{account.month:%Y-%m-%d}",
        "present_days": account.total_present,
        "absent_days": account.total_absent,
        "previous_advance": account.opening_balance,
    })

    return render(request, "staff/staff_account.html", {
        "staff": staff_member,
        "account": account,
        "attendance_formset": attendance_formset,
        "account_formset": account_formset,
        "account_rows": account_rows,
        "month_value": f"{account.month:%Y-%m}",
        "payslip_params": payslip_params,
    })


from django.shortcuts import render, redirect, get_object_or_404
from .models import Vehicle

# ================= VEHICLES =================
from datetime import date, timedelta # Ye line file mein sab se upar honi chahiye

VEHICLE_SORT_FIELDS = {
    "vehicle_number": "Vehicle Number",
    "driver__name": "Staff Name",
    "vendor__name": "Vendor Name",
    "vehicle_type__name": "Vehicle Type",
    "wheeler__name": "Wheeler",
    "current_location__name": "Current Location",
    "is_active": "Status",
}

# 1. List dikhane ke liye (UPDATED FOR ALERTS)
def vehicle_list(request):
    vehicles, sort_by, order = _sorted_queryset(
        request, Vehicle.objects.all(), VEHICLE_SORT_FIELDS, "vehicle_number"
    )

    # --- YEH LOGIC ADD KI HAI ALERTS KE LIYE ---
    today = date.today()
    warning_date = today + timedelta(days=15)

    context = {
        "vehicles": vehicles,
        "today": today,          # HTML mein isi naam se comparison ho raha hai
        "warning_date": warning_date,
        "sort_fields": VEHICLE_SORT_FIELDS,
        "sort_by": sort_by,
        "order": order,
    }
    # ------------------------------------------

    return render(request, "vehicle/vehicle_list.html", context)

# 2. Naya vehicle register karne ke liye
def vehicle_add(request):
    # Agar data POST hai toh form fill hoga, warna khali form
    form = VehicleForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("vehicle_list")

    # IMPORTANT: Template ka naam "vehicle_form.html" hona chahiye
    return render(request, "vehicle/vehicle_form.html", {"form": form})

# 3. Vehicle Edit karne ke liye
def vehicle_edit(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    # Instance pass karna zaroori hai taake purana data nazar aaye
    form = VehicleForm(request.POST or None, instance=vehicle)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("vehicle_list")

    return render(request, "vehicle/vehicle_form.html", {"form": form, "vehicle": vehicle})

# 4. Vehicle Delete karne ke liye
def vehicle_delete(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    vehicle.delete()
    return redirect("vehicle_list")


# ================= VEHICLE TYRES (separate page - Vehicle # first, rest auto-fills) =================
def vehicle_tyres_select(request):
    vehicles = Vehicle.objects.all().order_by("vehicle_number")
    return render(request, "vehicle/vehicle_tyres_select.html", {"vehicles": vehicles})


def vehicle_tyres(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    if request.method == "POST":
        form = VehicleTyreForm(request.POST, vehicle=vehicle)
        if form.is_valid():
            tyre = form.save(commit=False)
            tyre.vehicle = vehicle
            tyre.save()
            messages.success(request, f"Tyre '{tyre.tyre_number}' added successfully.")
            return redirect("vehicle_tyres", vehicle_id=vehicle.id)
    else:
        form = VehicleTyreForm(vehicle=vehicle)

    tyres = vehicle.tyres.all().order_by("-id")
    return render(request, "vehicle/vehicle_tyres.html", {
        "vehicle": vehicle,
        "form": form,
        "tyres": tyres,
    })


def vehicle_tyre_edit(request, vehicle_id, tyre_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    tyre = get_object_or_404(VehicleTyre, id=tyre_id, vehicle=vehicle)
    if request.method == "POST":
        form = VehicleTyreForm(request.POST, instance=tyre, vehicle=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, f"Tyre '{tyre.tyre_number}' updated successfully.")
        else:
            messages.error(request, "Could not update that tyre - check the highlighted field(s).")
    return redirect("vehicle_tyres", vehicle_id=vehicle.id)


def vehicle_tyre_delete(request, vehicle_id, tyre_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    tyre = get_object_or_404(VehicleTyre, id=tyre_id, vehicle=vehicle)
    if request.method == "POST":
        number = tyre.tyre_number
        tyre.delete()
        messages.success(request, f"Tyre '{number}' deleted successfully.")
    return redirect("vehicle_tyres", vehicle_id=vehicle.id)


# ================= VEHICLE PERMITS & COMPLIANCE (separate page - Vehicle # first, rest auto-fills) =================
def vehicle_permits_select(request):
    vehicles = Vehicle.objects.all().order_by("vehicle_number")
    return render(request, "vehicle/vehicle_permits_select.html", {"vehicles": vehicles})


def vehicle_permits(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    if request.method == "POST":
        form = VehiclePermitsForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, "Permits & Compliance updated successfully.")
            return redirect("vehicle_permits", vehicle_id=vehicle.id)
    else:
        form = VehiclePermitsForm(instance=vehicle)

    return render(request, "vehicle/vehicle_permits.html", {
        "vehicle": vehicle,
        "form": form,
    })


# ================= VEHICLE TYPE + WHEELER (admin-extensible registries, one shared page) =================
def vehicle_type_wheeler_config(request):
    vehicle_types = VehicleType.objects.all()
    wheelers = Wheeler.objects.all()

    if request.method == "POST":
        if "add_type" in request.POST:
            form = VehicleTypeForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, f"Vehicle Type '{form.instance.name}' registered successfully.")
            else:
                messages.error(request, "Could not register that Vehicle Type - it may already exist.")
        elif "add_wheeler" in request.POST:
            form = WheelerForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, f"Wheeler '{form.instance.name}' registered successfully.")
            else:
                messages.error(request, "Could not register that Wheeler - it may already exist.")
        return redirect("vehicle_type_wheeler_config")

    return render(request, "vehicle/vehicle_type_wheeler.html", {
        "vehicle_types": vehicle_types,
        "wheelers": wheelers,
    })


def vehicle_type_edit(request, type_id):
    vtype = get_object_or_404(VehicleType, id=type_id)
    if request.method == "POST":
        form = VehicleTypeForm(request.POST, instance=vtype)
        if form.is_valid():
            form.save()
            messages.success(request, f"Vehicle Type updated to '{vtype.name}'.")
        else:
            messages.error(request, "That Vehicle Type name is already registered.")
    return redirect("vehicle_type_wheeler_config")


def vehicle_type_delete(request, type_id):
    vtype = get_object_or_404(VehicleType, id=type_id)
    if request.method == "POST":
        try:
            name = vtype.name
            vtype.delete()
            messages.success(request, f"Vehicle Type '{name}' deleted successfully.")
        except ProtectedError:
            messages.error(request, f"Cannot delete '{vtype.name}' - it's still assigned to a vehicle.")
    return redirect("vehicle_type_wheeler_config")


def wheeler_edit(request, wheeler_id):
    wheeler = get_object_or_404(Wheeler, id=wheeler_id)
    if request.method == "POST":
        form = WheelerForm(request.POST, instance=wheeler)
        if form.is_valid():
            form.save()
            messages.success(request, f"Wheeler updated to '{wheeler.name}'.")
        else:
            messages.error(request, "That Wheeler name is already registered.")
    return redirect("vehicle_type_wheeler_config")


def wheeler_delete(request, wheeler_id):
    wheeler = get_object_or_404(Wheeler, id=wheeler_id)
    if request.method == "POST":
        try:
            name = wheeler.name
            wheeler.delete()
            messages.success(request, f"Wheeler '{name}' deleted successfully.")
        except ProtectedError:
            messages.error(request, f"Cannot delete '{wheeler.name}' - it's still assigned to a vehicle.")
    return redirect("vehicle_type_wheeler_config")


# ================= LOCATIONS (CITY + ROUTE) =================
def locations_master(request):
    cities = City.objects.all()
    routes = Route.objects.select_related("origin", "destination")

    if request.method == "POST":

        # ---- ADD CITY ----
        if "add_city" in request.POST:
            # Safe conversion: agar khali ho toh None ya 0 jaye
            lat = request.POST.get("latitude") or 0
            lng = request.POST.get("longitude") or 0
            city_name = (request.POST.get("city_name") or "").strip()
            city_code = (request.POST.get("city_code") or "").strip()

            if not city_name or not city_code:
                messages.error(request, "City name and code are both required.")
            elif len(city_code) > 3:
                messages.error(request, "City code cannot be more than 3 characters.")
            elif City.objects.filter(name__iexact=city_name).exists():
                messages.error(request, f"City '{city_name.upper()}' is already registered.")
            elif City.objects.filter(code__iexact=city_code).exists():
                messages.error(request, f"City code '{city_code.upper()}' is already registered.")
            else:
                # Model's save() uppercases name/code automatically.
                City.objects.create(
                    name=city_name,
                    code=city_code,
                    latitude=lat,
                    longitude=lng
                )
                messages.success(request, f"City '{city_name.upper()}' registered successfully.")
            return redirect("locations_master")

        # ---- ADD ROUTE (MANUAL KMs & TT HOURS) ----
        if "add_route" in request.POST:
            origin_id = request.POST.get("origin")
            dest_id = request.POST.get("destination")
            distance_km = request.POST.get("distance_km")
            tt_hours = request.POST.get("tt_hours") or None

            if not origin_id or not dest_id:
                messages.error(request, "Please select both Origin and Destination.")
            elif not distance_km:
                messages.error(request, "Please enter the distance in KMs.")
            elif Route.objects.filter(origin_id=origin_id, destination_id=dest_id).exists():
                messages.error(request, "This route already exists.")
            else:
                origin = City.objects.get(id=origin_id)
                destination = City.objects.get(id=dest_id)
                Route.objects.create(
                    origin=origin,
                    destination=destination,
                    distance_km=distance_km,
                    tt_hours=tt_hours,
                )
                messages.success(request, f"Route {origin.code}-{destination.code} registered successfully.")
            return redirect("locations_master")

    return render(request, "locations/locations.html", {
        "cities": cities,
        "routes": routes
    })


def city_edit(request, city_id):
    city = get_object_or_404(City, id=city_id)
    if request.method == "POST":
        city_name = (request.POST.get("city_name") or "").strip()
        city_code = (request.POST.get("city_code") or "").strip()

        if not city_name or not city_code:
            messages.error(request, "City name and code are both required.")
        elif len(city_code) > 3:
            messages.error(request, "City code cannot be more than 3 characters.")
        elif City.objects.exclude(id=city.id).filter(name__iexact=city_name).exists():
            messages.error(request, f"City '{city_name.upper()}' is already registered.")
        elif City.objects.exclude(id=city.id).filter(code__iexact=city_code).exists():
            messages.error(request, f"City code '{city_code.upper()}' is already registered.")
        else:
            city.name = city_name
            city.code = city_code
            city.save()
            messages.success(request, f"City '{city.name}' updated successfully.")
    return redirect("locations_master")


def city_delete(request, city_id):
    city = get_object_or_404(City, id=city_id)
    if request.method == "POST":
        try:
            name = city.name
            city.delete()
            messages.success(request, f"City '{name}' deleted successfully.")
        except ProtectedError:
            messages.error(
                request,
                f"Cannot delete '{city.name}' - a route using this city has active trips. "
                "Remove those trips first."
            )
    return redirect("locations_master")


def route_edit(request, route_id):
    route = get_object_or_404(Route, id=route_id)
    if request.method == "POST":
        origin_id = request.POST.get("origin")
        dest_id = request.POST.get("destination")
        distance_km = request.POST.get("distance_km")
        tt_hours = request.POST.get("tt_hours") or None

        if not origin_id or not dest_id:
            messages.error(request, "Please select both Origin and Destination.")
        elif not distance_km:
            messages.error(request, "Please enter the distance in KMs.")
        elif Route.objects.exclude(id=route.id).filter(origin_id=origin_id, destination_id=dest_id).exists():
            messages.error(request, "This route already exists.")
        else:
            route.origin = City.objects.get(id=origin_id)
            route.destination = City.objects.get(id=dest_id)
            route.distance_km = distance_km
            route.tt_hours = tt_hours
            route.save()
            messages.success(request, f"Route {route.route_code} updated successfully.")
    return redirect("locations_master")


def route_delete(request, route_id):
    route = get_object_or_404(Route, id=route_id)
    if request.method == "POST":
        try:
            code = route.route_code
            route.delete()
            messages.success(request, f"Route '{code}' deleted successfully.")
        except ProtectedError:
            messages.error(
                request,
                f"Cannot delete route '{route.route_code}' - it has active trips. "
                "Remove those trips first."
            )
    return redirect("locations_master")

# ================= SUPPLIERS (Vendor model) =================
VENDOR_SORT_FIELDS = {
    "name": "Supplier Name",
    "supplier_type__name": "Supplier Type",
    "poc1_phone": "Phone",
    "poc1_name": "Point of Contact",
}

def vendor_list(request):
    vendors, sort_by, order = _sorted_queryset(
        request, Vendor.objects.annotate(vehicle_count=Count("vehicles")), VENDOR_SORT_FIELDS, "name"
    )
    return render(request, "vendors/vendor_list.html", {
        "vendors": vendors,
        "sort_fields": VENDOR_SORT_FIELDS,
        "sort_by": sort_by,
        "order": order,
    })

def vendor_add(request):
    if request.method == "POST":
        form = VendorForm(request.POST)
        if form.is_valid():
            vendor = form.save()
            fuel_formset = VendorFuelPriceFormSet(request.POST, instance=vendor)
            if fuel_formset.is_valid():
                fuel_formset.save()
                return redirect("vendor_list")
        else:
            fuel_formset = VendorFuelPriceFormSet(request.POST)
    else:
        form = VendorForm()
        fuel_formset = VendorFuelPriceFormSet()
    return render(request, "vendors/vendor_form.html", {"form": form, "fuel_formset": fuel_formset})

# ✅ NAYA: Vendor Edit function
def vendor_edit(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    if request.method == "POST":
        form = VendorForm(request.POST, instance=vendor)
        fuel_formset = VendorFuelPriceFormSet(request.POST, instance=vendor)
        if form.is_valid() and fuel_formset.is_valid():
            form.save()
            fuel_formset.save()
            return redirect("vendor_list")
    else:
        form = VendorForm(instance=vendor)
        fuel_formset = VendorFuelPriceFormSet(instance=vendor)
    return render(request, "vendors/vendor_form.html", {"form": form, "vendor": vendor, "fuel_formset": fuel_formset})

# ✅ NAYA: Vendor Delete function
def vendor_delete(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    if request.method == "POST":
        vendor.delete()
        return redirect("vendor_list")
    # Agar galti se GET request aaye toh wapas list pe bhej do
    return redirect("vendor_list")


# ================= SUPPLIER TYPE (admin-extensible registry) =================
def supplier_type_config(request):
    supplier_types = SupplierType.objects.all()

    if request.method == "POST":
        form = SupplierTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Supplier Type '{form.instance.name}' registered successfully.")
        else:
            messages.error(request, "Could not register that Supplier Type - it may already exist.")
        return redirect("supplier_type_config")

    return render(request, "vendors/supplier_type_config.html", {
        "supplier_types": supplier_types,
    })


def supplier_type_edit(request, type_id):
    stype = get_object_or_404(SupplierType, id=type_id)
    if request.method == "POST":
        form = SupplierTypeForm(request.POST, instance=stype)
        if form.is_valid():
            form.save()
            messages.success(request, f"Supplier Type updated to '{stype.name}'.")
        else:
            messages.error(request, "That Supplier Type name is already registered.")
    return redirect("supplier_type_config")


def supplier_type_delete(request, type_id):
    stype = get_object_or_404(SupplierType, id=type_id)
    if request.method == "POST":
        try:
            name = stype.name
            stype.delete()
            messages.success(request, f"Supplier Type '{name}' deleted successfully.")
        except ProtectedError:
            messages.error(request, f"Cannot delete '{stype.name}' - it's still assigned to a supplier.")
    return redirect("supplier_type_config")


# ================= FUEL PRODUCT (admin-extensible registry, shared by Suppliers & Vehicles) =================
def fuel_product_config(request):
    fuel_products = FuelProduct.objects.all()

    if request.method == "POST":
        form = FuelProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Product '{form.instance.name}' registered successfully.")
        else:
            messages.error(request, "Could not register that Product - it may already exist.")
        return redirect("fuel_product_config")

    return render(request, "vendors/fuel_product_config.html", {
        "fuel_products": fuel_products,
    })


def fuel_product_edit(request, product_id):
    product = get_object_or_404(FuelProduct, id=product_id)
    if request.method == "POST":
        form = FuelProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"Product updated to '{product.name}'.")
        else:
            messages.error(request, "That Product name is already registered.")
    return redirect("fuel_product_config")


def fuel_product_delete(request, product_id):
    product = get_object_or_404(FuelProduct, id=product_id)
    if request.method == "POST":
        try:
            name = product.name
            product.delete()
            messages.success(request, f"Product '{name}' deleted successfully.")
        except ProtectedError:
            messages.error(request, f"Cannot delete '{product.name}' - it's still in use.")
    return redirect("fuel_product_config")

from django.shortcuts import render, redirect, get_object_or_404
from .models import Client, ClientType, ClientRate, DedicatedRate, Expense
from .forms import ClientForm, ClientTypeForm, ClientRateForm, DedicatedRateForm, ExpenseForm

# ================= CLIENTS =================
CLIENT_SORT_FIELDS = {
    "name": "Company Name",
    "client_type__name": "Client Type",
    "poc1_name": "Point of Contact",
    "ntn": "NTN",
    "billing_company": "Billing Company",
}

def client_list(request):
    clients, sort_by, order = _sorted_queryset(
        request, Client.objects.all(), CLIENT_SORT_FIELDS, "name"
    )
    return render(request, "clients/client_list.html", {
        "clients": clients,
        "sort_fields": CLIENT_SORT_FIELDS,
        "sort_by": sort_by,
        "order": order,
    })

def client_add(request):
    form = ClientForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("client_list")
    return render(request, "clients/client_form.html", {"form": form})

# ✅ NAYA: Client Edit function (Iske bagair error aa raha tha)
def client_edit(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect("client_list")
    else:
        form = ClientForm(instance=client)
    return render(request, "clients/client_form.html", {"form": form, "client": client})

# ✅ NAYA: Client Delete function
def client_delete(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    if request.method == "POST":
        client.delete()
        return redirect("client_list")
    return redirect("client_list")


# ================= CLIENT TYPE (admin-extensible registry) =================
def client_type_config(request):
    client_types = ClientType.objects.all()

    if request.method == "POST":
        form = ClientTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Client Type '{form.instance.name}' registered successfully.")
        else:
            messages.error(request, "Could not register that Client Type - it may already exist.")
        return redirect("client_type_config")

    return render(request, "clients/client_type_config.html", {
        "client_types": client_types,
    })


def client_type_edit(request, type_id):
    ctype = get_object_or_404(ClientType, id=type_id)
    if request.method == "POST":
        form = ClientTypeForm(request.POST, instance=ctype)
        if form.is_valid():
            form.save()
            messages.success(request, f"Client Type updated to '{ctype.name}'.")
        else:
            messages.error(request, "That Client Type name is already registered.")
    return redirect("client_type_config")


def client_type_delete(request, type_id):
    ctype = get_object_or_404(ClientType, id=type_id)
    if request.method == "POST":
        try:
            name = ctype.name
            ctype.delete()
            messages.success(request, f"Client Type '{name}' deleted successfully.")
        except ProtectedError:
            messages.error(request, f"Cannot delete '{ctype.name}' - it's still assigned to a client.")
    return redirect("client_type_config")

# ================= CLIENT RATE (fuel-price-indexed revision log) =================
def client_rates_select(request):
    clients = Client.objects.all().order_by("name")
    return render(request, "clients/client_rates_select.html", {"clients": clients})


def client_rates(request, client_id):
    client = get_object_or_404(Client, id=client_id)

    if request.method == "POST":
        form = ClientRateForm(request.POST)
        if form.is_valid():
            rate = form.save(commit=False)
            rate.client = client
            rate.save()
            messages.success(request, "Rate entry added successfully.")
            return redirect("client_rates", client_id=client.id)
    else:
        form = ClientRateForm()

    rates = ClientRate.objects.filter(client=client)

    # Latest revision per route (rates is already ordered route, then
    # -effective_date/-id via Meta.ordering, so the first hit per route here
    # is its most recent one) - the add-rate form's JS uses this to auto-fill
    # and lock Current Fuel Price/Current Rate once a route has a prior entry.
    last_by_route = {}
    for r in rates:
        if r.route_id not in last_by_route:
            last_by_route[r.route_id] = {
                "fuel_price": str(r.updated_fuel_price),
                "trip_cost": str(r.updated_trip_cost),
                "effective_percent": str(r.effective_percent),
            }

    dedicated_rates = DedicatedRate.objects.filter(client=client).select_related("vehicle", "route")
    dedicated_form = DedicatedRateForm(auto_id="id_ded_%s")
    routes_distance = {r.id: str(r.distance_km) for r in Route.objects.all()}

    return render(request, "clients/client_rates.html", {
        "client": client,
        "form": form,
        "rates": rates,
        "last_by_route_json": json.dumps(last_by_route),
        "dedicated_rates": dedicated_rates,
        "dedicated_form": dedicated_form,
        "routes_distance_json": json.dumps(routes_distance),
    })


def client_rate_edit(request, client_id, rate_id):
    client = get_object_or_404(Client, id=client_id)
    rate = get_object_or_404(ClientRate, id=rate_id, client=client)
    if request.method == "POST":
        form = ClientRateForm(request.POST, instance=rate)
        if form.is_valid():
            form.save()
            messages.success(request, "Rate entry updated successfully.")
        else:
            messages.error(request, "Could not update that rate entry - check the highlighted field(s).")
    return redirect("client_rates", client_id=client.id)


def client_rate_delete(request, client_id, rate_id):
    client = get_object_or_404(Client, id=client_id)
    rate = get_object_or_404(ClientRate, id=rate_id, client=client)
    if request.method == "POST":
        rate.delete()
        messages.success(request, "Rate entry deleted successfully.")
    return redirect("client_rates", client_id=client.id)


# ================= DEDICATED RATE (per-vehicle fixed + variable cost) =================
from django.urls import reverse


def _client_rates_redirect(client_id, mode=None):
    url = reverse("client_rates", args=[client_id])
    return redirect(f"{url}?mode={mode}" if mode else url)


def client_dedicated_rate_add(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    if request.method == "POST":
        form = DedicatedRateForm(request.POST)
        if form.is_valid():
            rate = form.save(commit=False)
            rate.client = client
            rate.save()
            messages.success(request, "Dedicated rate entry added successfully.")
        else:
            messages.error(request, "Could not add that dedicated rate entry - check the highlighted field(s).")
    return _client_rates_redirect(client.id, mode="dedicated")


def client_dedicated_rate_edit(request, client_id, rate_id):
    client = get_object_or_404(Client, id=client_id)
    rate = get_object_or_404(DedicatedRate, id=rate_id, client=client)
    if request.method == "POST":
        form = DedicatedRateForm(request.POST, instance=rate)
        if form.is_valid():
            form.save()
            messages.success(request, "Dedicated rate entry updated successfully.")
        else:
            messages.error(request, "Could not update that dedicated rate entry - check the highlighted field(s).")
    return _client_rates_redirect(client.id, mode="dedicated")


def client_dedicated_rate_delete(request, client_id, rate_id):
    client = get_object_or_404(Client, id=client_id)
    rate = get_object_or_404(DedicatedRate, id=rate_id, client=client)
    if request.method == "POST":
        rate.delete()
        messages.success(request, "Dedicated rate entry deleted successfully.")
    return _client_rates_redirect(client.id, mode="dedicated")

# ================= EXPENSES =================
def expense_edit(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    if request.method == "POST":
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            return redirect("expense_list")
    else:
        form = ExpenseForm(instance=expense)
    return render(request, "expenses/expense_form.html", {"form": form, "expense": expense})

def expense_delete(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    if request.method == "POST":
        expense.delete()
        return redirect("expense_list")
    return render(request, "expenses/expense_confirm_delete.html", {"expense": expense})

from django.shortcuts import render, redirect
from .forms import ExpenseForm
from .models import Expense

# ================= EXPENSE SHEET (ADD) =================
def expense_sheet(request):
    if request.method == "POST":
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("expense_list")
    else:
        form = ExpenseForm()

    return render(request, "expenses/expense_sheet.html", {
        "form": form
    })


# ================= EXPENSE LIST =================
EXPENSE_SORT_FIELDS = {
    "date": "Date",
    "total_expense": "Total Amount",
    "fuel_amount": "Fuel Amount",
    "toll_tax": "Toll Tax",
}

def expense_list(request):
    expenses, sort_by, order = _sorted_queryset(
        request, Expense.objects.all(), EXPENSE_SORT_FIELDS, "date", default_order="desc"
    )
    return render(request, "expenses/expense_list.html", {
        "expenses": expenses,
        "sort_fields": EXPENSE_SORT_FIELDS,
        "sort_by": sort_by,
        "order": order,
    })
# ================= EXPENSE EDIT & DELETE =================

def expense_edit(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    if request.method == "POST":
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            return redirect("expense_list")
    else:
        form = ExpenseForm(instance=expense)
    return render(request, "expenses/expense_sheet.html", {"form": form, "expense": expense})

def expense_delete(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    expense.delete()
    return redirect("expense_list")




# ================= SALARY =================
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

SALARY_SORT_FIELDS = {
    "emp_id": "Emp ID",
    "driver__name": "Employee Name",
    "month": "Month",
    "present_days": "Present Days",
    "absent_days": "Absent Days",
    "sundays": "Sundays",
    "base_salary": "Base Salary",
    "per_day_rate": "Per Day Rate",
    "earned_base_salary": "Earned Base Salary",
    "attendance_allowance": "Attendance Allowance",
    "total_gross_salary": "Total Gross Salary",
    "previous_advance": "Previous Advance",
    "new_advance_taken": "New Advance Taken",
    "advance_deduction": "Advance Deduction",
    "net_payable_salary": "Net Payable",
    "status": "Status",
    "paid": "Paid",
}

def salary_list(request):
    sort_by = request.GET.get("sort_by", "month")
    order = request.GET.get("order", "desc")
    if sort_by not in SALARY_SORT_FIELDS:
        sort_by = "month"
    if order not in ("asc", "desc"):
        order = "desc"

    order_field = sort_by if order == "asc" else f"-{sort_by}"
    salaries = DriverSalary.objects.select_related("driver").order_by(order_field)
    total_payout = salaries.aggregate(total=Sum("net_payable_salary"))["total"] or 0

    context = {
        "salaries": salaries,
        "total_payout": total_payout,
        "sort_fields": SALARY_SORT_FIELDS,
        "sort_by": sort_by,
        "order": order,
    }
    return render(request, "salary/salary_list.html", context)


def salary_slip_pdf(request, salary_id):
    salary = get_object_or_404(DriverSalary.objects.select_related("driver"), id=salary_id)

    template = get_template("salary/salary_slip_pdf.html")
    html = template.render({"s": salary, "issue_date": date.today()})

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="Salary_Slip_{salary.emp_id or salary.driver.employee_id}_'
        f'{salary.month.strftime("%b-%Y")}.pdf"'
    )

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse("PDF banane mein masla hua", status=400)
    return response


def salary_add(request):
    if request.method == "POST":
        form = DriverSalaryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("salary_list")
    else:
        # Prefilled from the Staff Monthly Account statement's "Generate
        # Payslip" button (?staff=&month=&present_days=&absent_days=&previous_advance=).
        initial = {}
        if request.GET.get("staff"):
            initial["driver"] = request.GET["staff"]
        if request.GET.get("month"):
            initial["month"] = request.GET["month"]
        for field in ("present_days", "absent_days", "previous_advance"):
            if request.GET.get(field):
                initial[field] = request.GET[field]
        form = DriverSalaryForm(initial=initial)
    return render(request, "salary/salary_form.html", {"form": form})


def salary_edit(request, salary_id):
    salary = get_object_or_404(DriverSalary, id=salary_id)
    form = DriverSalaryForm(request.POST or None, instance=salary)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("salary_list")
    return render(request, "salary/salary_form.html", {"form": form, "salary": salary})


def salary_delete(request, salary_id):
    salary = get_object_or_404(DriverSalary, id=salary_id)
    salary.delete()
    return redirect("salary_list")
