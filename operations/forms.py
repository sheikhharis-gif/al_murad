from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from .models import Job, Trip, JobExpense, JobFuelEntry
from masters.models import Vehicle, Client, Route, Vendor, FuelProduct

# -----------------------
# JOB FORM (header only - date, vehicle, trip advance, remarks)
# -----------------------
class VehicleJobChoiceField(forms.ModelChoiceField):
    """Shows each vehicle next to its current Job # if it already has a
    still-open one. The real number for a brand-new Job is only decided by
    the database at the moment it's actually created (AutoField), so it
    can't be previewed here - showing a guessed "next serial" made every
    vehicle without an open Job display the same fake number."""

    def label_from_instance(self, vehicle):
        open_job = (
            Job.objects.filter(vehicle=vehicle)
            .exclude(status__in=["completed", "cancelled"])
            .order_by("-job_number")
            .first()
        )
        if open_job:
            return f"JOB #{open_job.job_number:05d} | {vehicle.vehicle_number}"
        return f"NEW JOB | {vehicle.vehicle_number}"


class JobForm(forms.ModelForm):
    vehicle = VehicleJobChoiceField(queryset=Vehicle.objects.none(), required=False)

    # Not Job model fields - "Rental" just picks/creates a Vehicle record
    # (vehicle_mode="RENTAL") on the fly from a typed-in number instead of
    # requiring the vehicle be pre-registered in Vehicles master data first.
    # Everything downstream (Job.vehicle, Trip meter chaining, freight
    # matching, the invoice PDF's existing Own/Rental branch) then works
    # exactly as it already does for fleet vehicles - no schema change needed.
    is_rental = forms.BooleanField(
        required=False, label="Rental Vehicle",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "role": "switch", "id": "id_is_rental"}),
    )
    rental_vehicle_number = forms.CharField(
        required=False, label="Rental Vehicle Number",
        widget=forms.TextInput(attrs={
            "class": "form-control", "placeholder": "e.g. ABC-123", "data-uppercase": "1",
            "id": "id_rental_vehicle_number",
        }),
    )

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
        if self.instance.pk and self.instance.vehicle_id and self.instance.vehicle.vehicle_mode == "RENTAL":
            self.fields["is_rental"].initial = True
            self.fields["rental_vehicle_number"].initial = self.instance.vehicle.vehicle_number

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("is_rental"):
            number = (cleaned.get("rental_vehicle_number") or "").strip().upper()
            if not number:
                self.add_error("rental_vehicle_number", "Rental vehicle number is required.")
            else:
                vehicle, _ = Vehicle.objects.get_or_create(
                    vehicle_number=number, defaults={"vehicle_mode": "RENTAL"}
                )
                cleaned["vehicle"] = vehicle
        elif not cleaned.get("vehicle"):
            self.add_error("vehicle", "Please select a vehicle.")
        return cleaned


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
            # type="datetime-local"'s displayed AM/PM-vs-24hr format is fixed
            # by the browser's own UI language and can't be overridden from
            # the page at all (confirmed - lang="en-GB" on the element does
            # nothing in Chromium). Forcing 24-hour therefore needs flatpickr
            # (enhanceDatetimepickers in app.js, time_24hr:true) same as
            # before, but this time with clickOpens:false so focusing/typing
            # into the field no longer pops the calendar open over it -
            # typing straight into the box now works exactly like the native
            # widget did, it just displays/parses 24-hour text.
            "reached_at": forms.DateTimeInput(attrs={"class": "form-control form-control-sm datetimepicker"}, format="%Y-%m-%d %H:%M"),
            "departed_at": forms.DateTimeInput(attrs={"class": "form-control form-control-sm datetimepicker"}, format="%Y-%m-%d %H:%M"),
            "arrived_at": forms.DateTimeInput(attrs={"class": "form-control form-control-sm datetimepicker"}, format="%Y-%m-%d %H:%M"),
            "delivered_at": forms.DateTimeInput(attrs={"class": "form-control form-control-sm datetimepicker"}, format="%Y-%m-%d %H:%M"),
            "additional_charges": forms.NumberInput(attrs={"class": "form-control form-control-sm", "step": "0.01"}),
            "remarks": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Remarks"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["client"].queryset = Client.objects.filter(is_active=True).order_by("name")
        self.fields["client"].empty_label = "--- Select Client ---"
        self.fields["route"].queryset = Route.objects.all().order_by("route_code")
        self.fields["route"].empty_label = "--- Select Route ---"
        # New trips open with today's date pre-filled (it's still only saved
        # if the rest of the row is filled in - an untouched extra row stays
        # "unchanged" since the date matches its initial value).
        if not self.instance.pk and not self.initial.get("trip_date"):
            self.initial["trip_date"] = timezone.localdate()


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
