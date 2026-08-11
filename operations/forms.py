from django import forms
from django.forms import inlineformset_factory
from .models import Job, Trip, JobExpense, JobFuelEntry
from masters.models import Vehicle, Client, Route, Vendor, FuelProduct

# -----------------------
# JOB FORM (header only - date, vehicle, trip advance, remarks)
# -----------------------
class VehicleJobChoiceField(forms.ModelChoiceField):
    """Shows each vehicle next to its current Job # - the still-open Job if
    it has one, else the next Job # it will be assigned (last serial + 1)."""

    def label_from_instance(self, vehicle):
        open_job = (
            Job.objects.filter(vehicle=vehicle)
            .exclude(status__in=["completed", "cancelled"])
            .order_by("-job_number")
            .first()
        )
        if open_job:
            job_no = open_job.job_number
        else:
            last = Job.objects.order_by("-job_number").first()
            job_no = (last.job_number + 1) if last else 1
        return f"JOB #{job_no:05d} | {vehicle.vehicle_number}"


class JobForm(forms.ModelForm):
    vehicle = VehicleJobChoiceField(queryset=Vehicle.objects.none())

    class Meta:
        model = Job
        fields = ["vehicle", "job_date", "trip_advance", "remarks"]
        widgets = {
            "vehicle": forms.Select(attrs={"class": "form-select searchable-select", "autofocus": "autofocus"}),
            "job_date": forms.DateInput(attrs={"class": "form-control datepicker"}),
            "trip_advance": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Voyage details..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vehicle"].queryset = Vehicle.objects.filter(is_active=True).order_by("vehicle_number")
        self.fields["vehicle"].empty_label = "--- Select Vehicle ---"


# -----------------------
# TRIP FORM (one leg of a Job)
# -----------------------
class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = [
            "trip_date", "client", "bilty_number", "weight", "route",
            "reached_at", "departed_at", "arrived_at", "delivered_at",
            "additional_charges", "remarks",
        ]
        widgets = {
            "trip_date": forms.DateInput(attrs={"class": "form-control form-control-sm", "type": "date"}),
            "client": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "bilty_number": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Bilty #"}),
            "weight": forms.NumberInput(attrs={"class": "form-control form-control-sm", "step": "0.01", "placeholder": "Weight (Tons)"}),
            "route": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "reached_at": forms.DateTimeInput(attrs={"class": "form-control form-control-sm", "type": "datetime-local"}),
            "departed_at": forms.DateTimeInput(attrs={"class": "form-control form-control-sm", "type": "datetime-local"}),
            "arrived_at": forms.DateTimeInput(attrs={"class": "form-control form-control-sm", "type": "datetime-local"}),
            "delivered_at": forms.DateTimeInput(attrs={"class": "form-control form-control-sm", "type": "datetime-local"}),
            "additional_charges": forms.NumberInput(attrs={"class": "form-control form-control-sm", "step": "0.01"}),
            "remarks": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Remarks"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["client"].queryset = Client.objects.filter(is_active=True).order_by("name")
        self.fields["client"].empty_label = "--- Select Client ---"
        self.fields["route"].queryset = Route.objects.all().order_by("route_code")
        self.fields["route"].empty_label = "--- Select Route ---"


TripFormSet = inlineformset_factory(
    Job, Trip, form=TripForm, extra=1, can_delete=True,
)


# -----------------------
# JOB EXPENSE FORM (single shared breakdown per Job)
# -----------------------
class JobExpenseForm(forms.ModelForm):
    class Meta:
        model = JobExpense
        fields = [
            "toll_plaza", "food", "incentive", "mobile_expense", "challan",
            "tyre_expense", "service", "loading", "offloading", "weighbridge",
            "maintenance", "labor_charges", "fuel", "other", "remarks",
        ]
        widgets = {
            field: forms.NumberInput(attrs={"class": "form-control", "step": "0.01"})
            for field in [
                "toll_plaza", "food", "incentive", "mobile_expense", "challan",
                "tyre_expense", "service", "loading", "offloading", "weighbridge",
                "maintenance", "labor_charges", "fuel", "other",
            ]
        }
        widgets["remarks"] = forms.Textarea(attrs={"class": "form-control", "rows": 2})


# -----------------------
# JOB FUEL ENTRY FORM (multiple rows per Job)
# -----------------------
class JobFuelEntryForm(forms.ModelForm):
    class Meta:
        model = JobFuelEntry
        fields = ["supplier", "date", "product", "slip_number", "liters", "fuel_price"]
        widgets = {
            "supplier": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "date": forms.DateInput(attrs={"class": "form-control form-control-sm", "type": "date"}),
            "product": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "slip_number": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Slip #"}),
            "liters": forms.NumberInput(attrs={"class": "form-control form-control-sm", "step": "0.01"}),
            "fuel_price": forms.NumberInput(attrs={"class": "form-control form-control-sm", "step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["supplier"].queryset = Vendor.objects.filter(
            supplier_type__name="FUEL", is_active=True
        ).order_by("name")
        self.fields["supplier"].empty_label = "--- Select Fuel Supplier ---"
        self.fields["product"].queryset = FuelProduct.objects.all()
        self.fields["product"].empty_label = "--- Select Product ---"


JobFuelEntryFormSet = inlineformset_factory(
    Job, JobFuelEntry, form=JobFuelEntryForm, extra=1, can_delete=True,
)
