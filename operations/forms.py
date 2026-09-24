import datetime as dt
import json
from decimal import Decimal
from zoneinfo import ZoneInfo

from django import forms
from django.db.models import Q
from django.forms import inlineformset_factory
from django.utils import timezone
from .models import Job, Trip, JobExpense, JobFuelEntry
from masters.models import (
    Vehicle, VehicleType, Client, ClientSubCategory, Route, Vendor, FuelProduct, City, StopoverRate, stopover_amount,
)

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
class SubCategorySelect(forms.Select):
    """Sub-Category dropdown whose options remember which client they belong
    to (data-client), so the page can show only the chosen client's."""

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        instance = getattr(value, "instance", None)
        if instance is not None:
            option["attrs"]["data-client"] = instance.client_id
        return option


class StopoverCitySelect(forms.Select):
    """City dropdown whose options carry their stopover band (data-zone:
    KHI = within Karachi, OTHER), so the page can look up the charge."""

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        instance = getattr(value, "instance", None)
        if instance is not None:
            option["attrs"]["data-zone"] = instance.stopover_zone
        return option


class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = [
            "trip_date", "client", "sub_category", "bilty_number", "weight", "route", "vehicle_type",
            "reached_at", "departed_at", "arrived_at", "delivered_at",
            "stopover_city", "stopover_charges", "additional_charges", "remarks",
        ]
        widgets = {
            "trip_date": forms.DateInput(attrs={"class": "form-control form-control-sm", "type": "date"}),
            "client": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "sub_category": SubCategorySelect(attrs={"class": "form-select form-select-sm trip-subcategory"}),
            "bilty_number": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Bilty #"}),
            "weight": forms.NumberInput(attrs={"class": "form-control form-control-sm", "step": "0.01", "placeholder": "Weight (Tons)"}),
            "route": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "vehicle_type": forms.Select(attrs={
                "class": "form-select form-select-sm dropdown-search-select",
                "data-match": "contains", "data-theme": "light",
                "data-placeholder": "Type vehicle type...", "data-empty-text": "No matching vehicle type",
            }),
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
            "stopover_city": StopoverCitySelect(attrs={"class": "form-select form-select-sm trip-stopover-city"}),
            "stopover_charges": forms.NumberInput(attrs={
                "class": "form-control form-control-sm trip-stopover-charges", "step": "0.01", "placeholder": "Auto",
            }),
            "additional_charges": forms.NumberInput(attrs={"class": "form-control form-control-sm", "step": "0.01"}),
            "remarks": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Remarks"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Active clients, plus this trip's own client even if it's since been
        # deactivated - otherwise the trip could never be saved again.
        self.fields["client"].queryset = Client.objects.filter(
            Q(is_active=True) | Q(pk=self.instance.client_id)).order_by("name")
        self.fields["client"].empty_label = "--- Select Client ---"
        self.fields["sub_category"].queryset = ClientSubCategory.objects.filter(
            client__has_sub_categories=True).select_related("client").order_by("name")
        self.fields["sub_category"].empty_label = "--- Sub-Category ---"
        self.fields["stopover_city"].queryset = City.objects.order_by("name")
        self.fields["stopover_city"].empty_label = "--- No Stopover ---"
        # Left blank, the charge is filled in from the Stopover Rates table
        # (vehicle type x city band); typing a value overrides it.
        self.fields["stopover_charges"].required = False
        rates = {}
        for r in StopoverRate.objects.all():
            rates.setdefault(str(r.vehicle_type_id), {})[r.zone] = str(r.amount)
        self.fields["stopover_charges"].widget.attrs["data-rates"] = json.dumps(rates)
        self.fields["route"].queryset = Route.objects.all().order_by("route_code")
        self.fields["route"].empty_label = "--- Select Route ---"
        self.fields["vehicle_type"].queryset = VehicleType.objects.order_by("name")
        self.fields["vehicle_type"].empty_label = "--- Vehicle Type ---"
        # New trips open with today's date pre-filled (it's still only saved
        # if the rest of the row is filled in - an untouched extra row stays
        # "unchanged" since the date matches its initial value).
        if not self.instance.pk and not self.initial.get("trip_date"):
            # Server TIME_ZONE is UTC, so use Pakistan time for "today" -
            # otherwise trips added between 12am and 5am PKT default to yesterday.
            self.initial["trip_date"] = timezone.localdate(timezone=ZoneInfo("Asia/Karachi"))
        # ...and Reached Date & Time with the current Pakistan time. Saved
        # times are stored/shown as-is under the UTC setting (that's how
        # everyone already types them), so the Karachi wall-clock time is
        # labelled UTC rather than converted.
        if not self.instance.pk:
            now = timezone.localtime(timezone.now(), ZoneInfo("Asia/Karachi")).replace(
                tzinfo=dt.timezone.utc, second=0, microsecond=0)
            # Only Reached - the other three are filled in as the trip moves
            # on, and together they drive the trip's Status (At Loading ->
            # Departured -> Arrived -> Delivered).
            self.initial.setdefault("reached_at", now)

    def clean(self):
        cleaned = super().clean()
        client, sub = cleaned.get("client"), cleaned.get("sub_category")
        if sub and client and sub.client_id != client.pk:
            self.add_error("sub_category", f"{sub.name} doesn't belong to {client.name}.")
        elif client and not sub and client.has_sub_categories and client.sub_categories.exists():
            self.add_error("sub_category", f"{client.name} has sub-categories ({', '.join(s.name for s in client.sub_categories.all())}) - please choose one.")

        city, charges = cleaned.get("stopover_city"), cleaned.get("stopover_charges")
        if "stopover_charges" not in self.errors:
            if not city:
                if charges:
                    self.add_error("stopover_city", "Choose the stopover city these charges are for.")
                cleaned["stopover_charges"] = Decimal(0)
            elif charges is None:
                vt = cleaned.get("vehicle_type")
                cleaned["stopover_charges"] = stopover_amount(vt.pk if vt else None, city) or Decimal(0)
        return cleaned

    # Pre-filled on new rows, so on their own they don't count as "the user
    # filled this row in" - otherwise an untouched blank row would fail
    # validation (its time default moves on by the time the page is saved).
    AUTO_FILLED = {"trip_date", "reached_at", "departed_at", "arrived_at", "delivered_at", "vehicle_type"}

    def has_changed(self):
        if self.instance.pk:
            return super().has_changed()
        return any(name not in self.AUTO_FILLED for name in self.changed_data)


class BaseTripFormSet(forms.BaseInlineFormSet):
    def _construct_form(self, i, **kwargs):
        form = super()._construct_form(i, **kwargs)
        # Trip rows without a vehicle type yet (new rows) pre-select the job
        # vehicle's type; the user can change it per trip. Done here because
        # the job isn't attached to the form's instance until after __init__.
        vehicle = getattr(self.instance, "vehicle", None)
        if not form.instance.vehicle_type_id and vehicle and vehicle.vehicle_type_id:
            form.initial.setdefault("vehicle_type", vehicle.vehicle_type_id)
        # Rows added in the browser ("Add Trip") start on the vehicle's type too
        if vehicle and vehicle.vehicle_type_id:
            form.fields["vehicle_type"].widget.attrs["data-default"] = vehicle.vehicle_type_id
        return form


TripFormSet = inlineformset_factory(
    Job, Trip, form=TripForm, formset=BaseTripFormSet, extra=1, can_delete=True,
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
