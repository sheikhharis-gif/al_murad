from django.shortcuts import render, redirect
from django.db.models import Sum
from datetime import date

from .models import (
    Driver, Vehicle, City, Route,
    Vendor, Client, Expense,
    VehicleMaintenance, ClientRate, DriverSalary
)

from .forms import (
    DriverForm, VehicleForm,
    CityForm, RouteForm,
    VendorForm, ClientForm,
    ExpenseForm, ClientRateForm,
    DriverSalaryForm
)

from .utils import calculate_distance


# ================= DRIVERS =================
def driver_list(request):
    drivers = Driver.objects.all()
    return render(request, "drivers/driver_list.html", {"drivers": drivers})


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
from .forms import VehicleForm

# ================= VEHICLES =================
from datetime import date, timedelta # Ye line file mein sab se upar honi chahiye

# 1. List dikhane ke liye (UPDATED FOR ALERTS)
def vehicle_list(request):
    vehicles = Vehicle.objects.all()
    
    # --- YEH LOGIC ADD KI HAI ALERTS KE LIYE ---
    today = date.today()
    warning_date = today + timedelta(days=15)
    
    context = {
        "vehicles": vehicles,
        "today": today,          # HTML mein isi naam se comparison ho raha hai
        "warning_date": warning_date,
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
            
            City.objects.create(
                name=request.POST.get("city_name"),
                code=request.POST.get("city_code"),
                latitude=lat,
                longitude=lng
            )
            return redirect("locations_master")

        # ---- ADD ROUTE (AUTO DISTANCE) ----
        if "add_route" in request.POST:
            origin_id = request.POST.get("origin")
            dest_id = request.POST.get("destination")

            if origin_id and dest_id:
                origin = City.objects.get(id=origin_id)
                destination = City.objects.get(id=dest_id)

                # Check karein ke lat/lng mojood hain
                if origin.latitude and destination.latitude:
                    distance = calculate_distance(
                        origin.latitude, origin.longitude,
                        destination.latitude, destination.longitude
                    )
                else:
                    distance = 0  # Default agar coordinates na hon

                Route.objects.create(
                    origin=origin,
                    destination=destination,
                    distance_km=distance
                )
            return redirect("locations_master")

    return render(request, "locations/locations.html", {
        "cities": cities,
        "routes": routes
    })

# ================= VENDORS =================
def vendor_list(request):
    vendors = Vendor.objects.all()
    return render(request, "vendors/vendor_list.html", {"vendors": vendors})

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
def client_list(request):
    return render(request, "clients/client_list.html", {
        "clients": Client.objects.all()
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

    rates = ClientRate.objects.filter(client=client)

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
def expense_list(request):
    expenses = Expense.objects.all().order_by("-date")
    return render(request, "expenses/expense_list.html", {
        "expenses": expenses
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


# ================= MAINTENANCE =================
from django.shortcuts import render, redirect
from .models import VehicleMaintenance
from masters.models import Vehicle

def maintenance_list(request):
    # Use correct field 'change_date'
    records = VehicleMaintenance.objects.all().order_by("-change_date")
    return render(request, "maintenance/maintenance_list.html", {
        "records": records
    })


def maintenance_add(request):
    vehicles = Vehicle.objects.all()

    if request.method == "POST":
        VehicleMaintenance.objects.create(
            vehicle_id=request.POST.get("vehicle"),
            maintenance_type=request.POST.get("maintenance_type"),
            change_date=request.POST.get("change_date"),
            change_km=request.POST.get("change_km"),
            next_due_date=request.POST.get("next_due_date") or None,
            remarks=request.POST.get("remarks") or ""
        )
        return redirect("maintenance_list")

    return render(request, "maintenance/maintenance_form.html", {
        "vehicles": vehicles
    })


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
