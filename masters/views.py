from django.contrib import messages
from django.shortcuts import render, redirect
from django.db.models import Sum
from django.db.models.deletion import ProtectedError
from datetime import date

from .models import (
    Driver, Vehicle, VehicleType, Wheeler, City, Route,
    Vendor, Client, Expense,
    ClientRate, DriverSalary
)

from .forms import (
    DriverForm, VehicleForm, VehicleTyreFormSet,
    VehicleTypeForm, WheelerForm,
    CityForm, RouteForm,
    VendorForm, ClientForm,
    ExpenseForm, ClientRateForm,
    DriverSalaryForm
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


# ================= DRIVERS =================
DRIVER_SORT_FIELDS = {
    "name": "Driver Name",
    "employee_id": "Employee ID",
    "mobile": "Mobile Number",
    "cnic": "CNIC",
    "joining_date": "Joining Date",
    "is_active": "Status",
}

def driver_list(request):
    drivers, sort_by, order = _sorted_queryset(
        request, Driver.objects.all(), DRIVER_SORT_FIELDS, "name"
    )
    return render(request, "drivers/driver_list.html", {
        "drivers": drivers,
        "sort_fields": DRIVER_SORT_FIELDS,
        "sort_by": sort_by,
        "order": order,
    })


def driver_add(request):
    form = DriverForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("driver_list")
    return render(request, "drivers/driver_form.html", {"form": form})
# ================= DRIVER EDIT & DELETE =================

def driver_edit(request, driver_id):
    driver = get_object_or_404(Driver, id=driver_id)
    if request.method == "POST":
        form = DriverForm(request.POST, instance=driver)
        if form.is_valid():
            form.save()
            return redirect("driver_list")
    else:
        form = DriverForm(instance=driver)
    return render(request, "drivers/driver_form.html", {"form": form, "driver": driver})

def driver_delete(request, driver_id):
    driver = get_object_or_404(Driver, id=driver_id)
    driver.delete()
    return redirect("driver_list")


from django.shortcuts import render, redirect, get_object_or_404
from .models import Vehicle

# ================= VEHICLES =================
from datetime import date, timedelta # Ye line file mein sab se upar honi chahiye

VEHICLE_SORT_FIELDS = {
    "vehicle_number": "Vehicle Number",
    "driver__name": "Driver Name",
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
    tyre_formset = VehicleTyreFormSet(request.POST or None, prefix="tyres")
    if request.method == "POST" and form.is_valid() and tyre_formset.is_valid():
        vehicle = form.save()
        tyre_formset.instance = vehicle
        tyre_formset.save()
        return redirect("vehicle_list")

    # IMPORTANT: Template ka naam "vehicle_form.html" hona chahiye
    return render(request, "vehicle/vehicle_form.html", {"form": form, "tyre_formset": tyre_formset})

# 3. Vehicle Edit karne ke liye
def vehicle_edit(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    # Instance pass karna zaroori hai taake purana data nazar aaye
    form = VehicleForm(request.POST or None, instance=vehicle)
    tyre_formset = VehicleTyreFormSet(request.POST or None, instance=vehicle, prefix="tyres")

    if request.method == "POST" and form.is_valid() and tyre_formset.is_valid():
        form.save()
        tyre_formset.save()
        return redirect("vehicle_list")

    return render(request, "vehicle/vehicle_form.html", {"form": form, "vehicle": vehicle, "tyre_formset": tyre_formset})

# 4. Vehicle Delete karne ke liye
def vehicle_delete(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    vehicle.delete()
    return redirect("vehicle_list")


# ================= VEHICLE TYPE & WHEELER (admin-extensible registries) =================
def vehicle_type_config(request):
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
        return redirect("vehicle_type_config")

    return render(request, "vehicle/vehicle_type_config.html", {
        "vehicle_types": vehicle_types,
        "wheelers": wheelers,
        "type_form": VehicleTypeForm(),
        "wheeler_form": WheelerForm(),
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
    return redirect("vehicle_type_config")


def vehicle_type_delete(request, type_id):
    vtype = get_object_or_404(VehicleType, id=type_id)
    if request.method == "POST":
        try:
            name = vtype.name
            vtype.delete()
            messages.success(request, f"Vehicle Type '{name}' deleted successfully.")
        except ProtectedError:
            messages.error(request, f"Cannot delete '{vtype.name}' - it's still assigned to a vehicle.")
    return redirect("vehicle_type_config")


def wheeler_edit(request, wheeler_id):
    wheeler = get_object_or_404(Wheeler, id=wheeler_id)
    if request.method == "POST":
        form = WheelerForm(request.POST, instance=wheeler)
        if form.is_valid():
            form.save()
            messages.success(request, f"Wheeler updated to '{wheeler.name}'.")
        else:
            messages.error(request, "That Wheeler name is already registered.")
    return redirect("vehicle_type_config")


def wheeler_delete(request, wheeler_id):
    wheeler = get_object_or_404(Wheeler, id=wheeler_id)
    if request.method == "POST":
        try:
            name = wheeler.name
            wheeler.delete()
            messages.success(request, f"Wheeler '{name}' deleted successfully.")
        except ProtectedError:
            messages.error(request, f"Cannot delete '{wheeler.name}' - it's still assigned to a vehicle.")
    return redirect("vehicle_type_config")


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
            elif origin_id == dest_id:
                messages.error(request, "Origin and Destination cannot be the same city.")
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
        elif origin_id == dest_id:
            messages.error(request, "Origin and Destination cannot be the same city.")
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

# ================= VENDORS =================
VENDOR_SORT_FIELDS = {
    "name": "Vendor Name",
    "phone": "Phone",
    "poc": "Point of Contact",
}

def vendor_list(request):
    vendors, sort_by, order = _sorted_queryset(
        request, Vendor.objects.all(), VENDOR_SORT_FIELDS, "name"
    )
    return render(request, "vendors/vendor_list.html", {
        "vendors": vendors,
        "sort_fields": VENDOR_SORT_FIELDS,
        "sort_by": sort_by,
        "order": order,
    })

def vendor_add(request):
    form = VendorForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("vendor_list")
    return render(request, "vendors/vendor_form.html", {"form": form})

# ✅ NAYA: Vendor Edit function
def vendor_edit(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    if request.method == "POST":
        form = VendorForm(request.POST, instance=vendor)
        if form.is_valid():
            form.save()
            return redirect("vendor_list")
    else:
        form = VendorForm(instance=vendor)
    return render(request, "vendors/vendor_form.html", {"form": form, "vendor": vendor})

# ✅ NAYA: Vendor Delete function
def vendor_delete(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    if request.method == "POST":
        vendor.delete()
        return redirect("vendor_list")
    # Agar galti se GET request aaye toh wapas list pe bhej do
    return redirect("vendor_list")

from django.shortcuts import render, redirect, get_object_or_404
from .models import Client, ClientRate, Expense
from .forms import ClientForm, ClientRateForm, ExpenseForm

# ================= CLIENTS =================
CLIENT_SORT_FIELDS = {
    "name": "Company Name",
    "poc": "Point of Contact",
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

# ================= CLIENT RATE =================
def client_rates(request, client_id):
    client = get_object_or_404(Client, id=client_id)

    if request.method == "POST":
        form = ClientRateForm(request.POST)
        if form.is_valid():
            rate = form.save(commit=False)
            rate.client = client
            rate.save()
            return redirect("client_rates", client_id=client.id)
    else:
        form = ClientRateForm()

    rates = ClientRate.objects.filter(client=client).order_by("rate")

    return render(request, "clients/client_rates.html", {
        "client": client,
        "form": form,
        "rates": rates
    })

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
    form = DriverSalaryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("salary_list")
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
