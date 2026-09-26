from decimal import Decimal, InvalidOperation
from django import forms
from django.utils import timezone
from django.forms import modelformset_factory
from .models import (
    Vehicle, VehicleType, Wheeler, VehicleTyre, Staff, Vendor, SupplierType,
    City, Route, Client, ClientType, Company, TaxSettings, Expense, ClientRate, ClientSubCategory, DedicatedRate,
    DriverSalary, StaffAttendanceEntry, StaffAccountEntry, FuelProduct, VendorFuelPrice,
)
from django.forms import inlineformset_factory
from operations.models import Trip

################ VEHICLES ################

class VehicleForm(forms.ModelForm):
    # Declared explicitly (instead of the auto-generated DecimalField) so a
    # comma-formatted "7,500,000" doesn't fail Decimal parsing before
    # clean_value() gets a chance to strip the commas.
    value = forms.CharField(required=False, widget=forms.TextInput(attrs={
        "class": "form-control money-input", "placeholder": "e.g. 7,500,000", "inputmode": "numeric",
    }))

    class Meta:
        model = Vehicle
        # Permit/fitness expiry dates moved to their own "Permits & Compliance"
        # page (VehiclePermitsForm below) - excluded here so saving the main
        # Vehicle Registration form no longer touches (and can't blank out) them.
        exclude = [
            "sindh_permit_expiry", "punjab_permit_expiry", "kpk_permit_expiry",
            "balochistan_permit_expiry", "fitness_expiry_sindh", "fitness_expiry_punjab",
            "fitness_expiry_kpk", "fitness_expiry_balochistan",
        ]

        # 1. Purani driver fields ko list se nikaal diya, ab sirf 'driver' dropdown bacha hai
        text_fields = [
            "vehicle_number", "engine_no", "chassis_no", "container_no",
            "color", "starting_km", "current_km", "make", "registration_name", "m_tag",
            "owner", "weight_capacity",
        ]

        date_fields = ["purchase_date"]

        # 2. Base widgets for text fields
        widgets = {
            field: forms.TextInput(attrs={"class": "form-control text-uppercase"}) for field in text_fields
        }

        # 3. Date fields widgets
        widgets.update({
            field: forms.DateInput(attrs={"class": "form-control datepicker"}) for field in date_fields
        })

        # 4. Dropdowns (is mein ab 'driver' bhi shamil hai)
        widgets.update({
            "vendor": forms.Select(attrs={"class": "form-select"}),
            "driver": forms.Select(attrs={"class": "form-select searchable-select"}), # Naya Driver Dropdown
            "driver2": forms.Select(attrs={"class": "form-select searchable-select"}),
            "vehicle_mode": forms.Select(attrs={"class": "form-select", "autofocus": "autofocus"}),
            "vehicle_type": forms.Select(attrs={"class": "form-select"}),
            "wheeler": forms.Select(attrs={"class": "form-select"}),
            "fuel_type": forms.Select(attrs={"class": "form-select"}),
            "current_location": forms.Select(attrs={"class": "form-select"}),
            "dedicated_client": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "leased": forms.Select(attrs={"class": "form-select"}, choices=((False, "No"), (True, "Yes"))),
            "model_year": forms.NumberInput(attrs={"class": "form-control", "placeholder": "e.g. 2014"}),
        })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active staff when assigning one to a vehicle, A-Z (Staff.Meta.ordering).
        active_staff = Staff.objects.filter(is_active=True)
        if self.instance and self.instance.pk and self.instance.driver_id:
            # Keep the currently assigned staff member selectable even if they've since gone inactive.
            active_staff = active_staff | Staff.objects.filter(pk=self.instance.driver_id)
        if self.instance and self.instance.pk and self.instance.driver2_id:
            active_staff = active_staff | Staff.objects.filter(pk=self.instance.driver2_id)
        active_staff = active_staff.distinct()
        self.fields["driver"].queryset = active_staff
        self.fields["driver"].empty_label = "--- No Staff Assigned ---"
        self.fields["driver2"].queryset = active_staff
        self.fields["driver2"].empty_label = "--- No Second Staff ---"

        self.fields["vendor"].empty_label = "--- No Supplier ---"
        self.fields["vehicle_type"].empty_label = "--- Select Type ---"
        self.fields["wheeler"].empty_label = "--- Select Wheeler ---"
        self.fields["fuel_type"].empty_label = "--- Select Fuel Type ---"
        self.fields["current_location"].empty_label = "--- Select City ---"
        self.fields["dedicated_client"].empty_label = "--- Not Dedicated ---"

    def clean_value(self):
        # Value is typed with thousands-comma formatting (e.g. "7,500,000") for
        # readability - strip commas before handing it to the model's DecimalField.
        raw = (self.cleaned_data.get("value") or "").replace(",", "").strip()
        if not raw:
            return None
        try:
            return Decimal(raw)
        except InvalidOperation:
            raise forms.ValidationError("Enter a valid amount.")


class VehiclePermitsForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            "sindh_permit_expiry", "fitness_expiry_sindh",
            "punjab_permit_expiry", "fitness_expiry_punjab",
            "kpk_permit_expiry", "fitness_expiry_kpk",
            "balochistan_permit_expiry", "fitness_expiry_balochistan",
        ]
        widgets = {
            field: forms.DateInput(attrs={"class": "form-control datepicker"}) for field in fields
        }


class VehicleTyreForm(forms.ModelForm):
    class Meta:
        model = VehicleTyre
        fields = ["make", "tyre_number", "installed_date", "installed_km", "price"]
        widgets = {
            "make": forms.TextInput(attrs={"class": "form-control text-uppercase", "placeholder": "Tyre make", "autofocus": "autofocus"}),
            "tyre_number": forms.TextInput(attrs={"class": "form-control text-uppercase", "placeholder": "Tyre number"}),
            "installed_date": forms.DateInput(attrs={"class": "form-control datepicker"}),
            "installed_km": forms.NumberInput(attrs={"class": "form-control", "placeholder": "KM", "min": "0"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Price", "min": "0", "step": "0.01"}),
        }

    def __init__(self, *args, vehicle=None, **kwargs):
        # 'vehicle' is passed explicitly by the view (not part of POST data)
        # so clean_tyre_number() can scope the duplicate check per-vehicle.
        self.vehicle = vehicle
        super().__init__(*args, **kwargs)

    def clean_tyre_number(self):
        number = (self.cleaned_data.get("tyre_number") or "").strip().upper()
        if self.vehicle:
            qs = VehicleTyre.objects.filter(vehicle=self.vehicle, tyre_number=number)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("This tyre number is already registered for this vehicle.")
        return number


class VehicleTypeForm(forms.ModelForm):
    class Meta:
        model = VehicleType
        fields = ["name"]
        widgets = {"name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 20FT DRY", "autofocus": "autofocus"})}

    def clean_name(self):
        # Model.save() uppercases the name, so the duplicate check must compare
        # uppercased too - otherwise "45ft dry" slips past validation as "unique"
        # and then collides with the already-uppercased "45FT DRY" at save time.
        name = (self.cleaned_data.get("name") or "").strip().upper()
        qs = VehicleType.objects.filter(name=name)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This Vehicle Type is already registered.")
        return name


class WheelerForm(forms.ModelForm):
    class Meta:
        model = Wheeler
        fields = ["name"]
        widgets = {"name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 10 WHEELER"})}

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip().upper()
        qs = Wheeler.objects.filter(name=name)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This Wheeler is already registered.")
        return name

################ DRIVERS ################

class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = "__all__"
        widgets = {
            field: forms.TextInput(attrs={"class": "form-control"})
            for field in [
                "name", "father_name", "designation", "mobile1", "mobile2", "cnic",
                "license_number", "license_category", "reference1_name",
                "reference1_mobile", "reference2_name", "reference2_mobile",
                "next_of_kin_name", "next_of_kin_mobile", "next_of_kin_relation",
            ]
        }
        widgets["designation"].attrs["autofocus"] = "autofocus"
        widgets.update({
            "salary": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["address"].widget = forms.Textarea(attrs={"class": "form-control", "rows": 3})
        self.fields["date_of_birth"].widget = forms.DateInput(attrs={"class": "form-control datepicker"})
        self.fields["cnic_expiry"].widget = forms.DateInput(attrs={"class": "form-control datepicker"})
        self.fields["license_expiry"].widget = forms.DateInput(attrs={"class": "form-control datepicker"})
        self.fields["joining_date"].widget = forms.DateInput(attrs={"class": "form-control datepicker"})
        self.fields["is_active"].widget.attrs.update({"class": "form-check-input"})

################ SALARY ################

class DriverSalaryForm(forms.ModelForm):
    class Meta:
        model = DriverSalary
        fields = "__all__"
        widgets = {
            "driver": forms.Select(attrs={"class": "form-select", "autofocus": "autofocus"}),
            "month": forms.DateInput(attrs={"class": "form-control datepicker"}),
            "emp_id": forms.TextInput(attrs={"class": "form-control"}),
            "designation": forms.TextInput(attrs={"class": "form-control"}),
            "present_days": forms.NumberInput(attrs={"class": "form-control"}),
            "absent_days": forms.NumberInput(attrs={"class": "form-control"}),
            "sundays": forms.NumberInput(attrs={"class": "form-control"}),
            "base_salary": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "per_day_rate": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "earned_base_salary": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "attendance_allowance": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "total_gross_salary": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "previous_advance": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "new_advance_taken": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "advance_deduction": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "net_payable_salary": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "status": forms.TextInput(attrs={"class": "form-control"}),
            "paid": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

################ STAFF MONTHLY ACCOUNT & EXPENSE STATEMENT ################

class StaffAttendanceEntryForm(forms.ModelForm):
    class Meta:
        model = StaffAttendanceEntry
        fields = ["status", "remarks"]
        widgets = {
            # RadioSelect (not a dropdown) so the template can lay Present/Leave/Absent
            # out as three separate columns, matching the "STAFF" spreadsheet format.
            "status": forms.RadioSelect(attrs={"class": "form-check-input"}),
            "remarks": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Remarks"}),
        }


StaffAttendanceFormSet = modelformset_factory(
    StaffAttendanceEntry, form=StaffAttendanceEntryForm, extra=0,
)


class StaffAccountEntryForm(forms.ModelForm):
    class Meta:
        model = StaffAccountEntry
        fields = ["date", "amount", "paid", "expense", "remarks"]
        widgets = {
            "date": forms.DateInput(attrs={"class": "form-control form-control-sm datepicker"}),
            "amount": forms.NumberInput(attrs={"class": "form-control form-control-sm", "step": "0.01"}),
            "paid": forms.NumberInput(attrs={"class": "form-control form-control-sm", "step": "0.01"}),
            "expense": forms.NumberInput(attrs={"class": "form-control form-control-sm", "step": "0.01"}),
            "remarks": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Remarks"}),
        }


StaffAccountEntryFormSet = modelformset_factory(
    StaffAccountEntry, form=StaffAccountEntryForm, extra=1, can_delete=True,
)

################ MASTERS ################

class CityForm(forms.ModelForm):
    class Meta:
        model = City
        fields = "__all__"
        widgets = {"name": forms.TextInput(attrs={"class": "form-control"})}

class RouteForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = "__all__"
        widgets = {
            "origin": forms.Select(attrs={"class": "form-select searchable-select"}),
            "destination": forms.Select(attrs={"class": "form-select searchable-select"}),
            "distance_km": forms.NumberInput(attrs={"class": "form-control"}),
        }

################ SUPPLIER (Vendor model) & CLIENT ################

class SupplierTypeForm(forms.ModelForm):
    class Meta:
        model = SupplierType
        fields = ["name"]
        widgets = {"name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. FUEL STATION"})}

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip().upper()
        qs = SupplierType.objects.filter(name=name)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This Supplier Type is already registered.")
        return name


class SupplierTypeSelect(forms.Select):
    # Tags each <option> with data-name="<SUPPLIER TYPE NAME>" so the Vendor
    # form's JS can show/hide the Fuel Prices section without a page reload
    # when Supplier Type = FUEL is picked.
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        raw_value = getattr(value, "value", value)
        if raw_value:
            supplier_type = SupplierType.objects.filter(pk=raw_value).values_list("name", flat=True).first()
            if supplier_type:
                option["attrs"]["data-name"] = supplier_type
        return option


class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = "__all__"

        text_fields = [
            "name", "poc1_name", "poc1_phone", "poc2_name", "poc2_phone",
            "ntn", "stn", "term_of_service", "billing_period",
        ]
        uppercase_fields = [
            "name", "poc1_name", "poc2_name", "ntn", "stn", "term_of_service", "billing_period",
        ]

        widgets = {
            field: forms.TextInput(attrs={"class": "form-control text-uppercase"}) for field in text_fields
        }
        for field in uppercase_fields:
            widgets[field].attrs["data-uppercase"] = "1"
        widgets["name"].attrs["autofocus"] = "autofocus"
        widgets.update({
            "supplier_type": SupplierTypeSelect(attrs={"class": "form-select", "id": "id_supplier_type"}),
            "poc1_email": forms.EmailInput(attrs={"class": "form-control text-uppercase", "data-uppercase": "1"}),
            "poc2_email": forms.EmailInput(attrs={"class": "form-control text-uppercase", "data-uppercase": "1"}),
            "address": forms.Textarea(attrs={"class": "form-control text-uppercase", "rows": 3, "data-uppercase": "1"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["supplier_type"].empty_label = "--- Select Supplier Type ---"


class FuelProductForm(forms.ModelForm):
    class Meta:
        model = FuelProduct
        fields = ["name"]
        widgets = {"name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. HI CETANE", "autofocus": "autofocus"})}

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip().upper()
        qs = FuelProduct.objects.filter(name=name)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This Product is already registered.")
        return name


class PsoFuelPriceForm(forms.Form):
    """PSO is fixed and hidden (no supplier picker) - just a date plus the
    two fuel prices the client actually bills against: Premier Euro5 and
    Hi-Cetane Diesel Euro5."""
    effective_date = forms.DateField(widget=forms.DateInput(attrs={
        "class": "form-control datepicker", "autofocus": "autofocus",
    }))
    premier_price = forms.DecimalField(
        max_digits=10, decimal_places=2, required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "e.g. 391.22"}),
    )
    hi_cetane_price = forms.DecimalField(
        max_digits=10, decimal_places=2, required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "e.g. 421.45"}),
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("premier_price") is None and cleaned.get("hi_cetane_price") is None:
            raise forms.ValidationError("Enter at least one of Premier Euro5 or Hi-Cetane Diesel Euro5 price.")
        return cleaned


class FuelRateForm(forms.ModelForm):
    class Meta:
        model = VendorFuelPrice
        fields = ["vendor", "product", "fuel_price", "effective_date"]
        widgets = {
            "vendor": forms.Select(attrs={"class": "form-select"}),
            "product": forms.Select(attrs={"class": "form-select"}),
            "fuel_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "e.g. 395.95"}),
            "effective_date": forms.DateInput(attrs={"class": "form-control datepicker"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vendor"].queryset = Vendor.objects.filter(
            supplier_type__name="FUEL", is_active=True
        ).order_by("name")
        self.fields["vendor"].empty_label = "--- Select Fuel Supplier ---"
        self.fields["product"].queryset = FuelProduct.objects.all().order_by("name")
        self.fields["product"].empty_label = "--- Select Fuel Product ---"
        if not self.instance.pk:
            self.initial["effective_date"] = timezone.localdate()


VendorFuelPriceFormSet = inlineformset_factory(
    Vendor,
    VendorFuelPrice,
    fields=["product", "fuel_price", "effective_date"],
    widgets={
        "product": forms.Select(attrs={"class": "form-select form-select-sm"}),
        "fuel_price": forms.NumberInput(attrs={"class": "form-control form-control-sm", "step": "0.01", "placeholder": "Fuel Price"}),
        "effective_date": forms.DateInput(attrs={"class": "form-control form-control-sm datepicker"}),
    },
    extra=1,
    can_delete=True,
)

class ClientTypeForm(forms.ModelForm):
    class Meta:
        model = ClientType
        fields = ["name"]
        widgets = {"name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. CORPORATE"})}

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip().upper()
        qs = ClientType.objects.filter(name=name)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This Client Type is already registered.")
        return name


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        # Has Sub-Categories / Has Stopover Charges live on the Client Rates
        # page - left out here so saving a client never resets them.
        exclude = ["has_sub_categories", "has_stopover"]

        text_fields = [
            "name", "poc1_name", "poc1_phone", "poc2_name", "poc2_phone",
            "ntn", "stn", "term_of_service", "billing_period", "billing_company",
        ]
        uppercase_fields = [
            "name", "poc1_name", "poc2_name", "ntn", "stn",
            "term_of_service", "billing_period", "billing_company",
        ]

        widgets = {
            field: forms.TextInput(attrs={"class": "form-control text-uppercase"}) for field in text_fields
        }
        for field in uppercase_fields:
            widgets[field].attrs["data-uppercase"] = "1"
        widgets["name"].attrs["autofocus"] = "autofocus"
        widgets.update({
            "client_type": forms.Select(attrs={"class": "form-select"}),
            "poc1_email": forms.EmailInput(attrs={"class": "form-control text-uppercase", "data-uppercase": "1"}),
            "poc2_email": forms.EmailInput(attrs={"class": "form-control text-uppercase", "data-uppercase": "1"}),
            "address": forms.Textarea(attrs={"class": "form-control text-uppercase", "rows": 3, "data-uppercase": "1"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["client_type"].empty_label = "--- Select Client Type ---"


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = "__all__"

        text_fields = ["name", "poc1_name", "poc1_phone", "poc2_name", "poc2_phone", "ntn", "stn"]
        uppercase_fields = ["name", "poc1_name", "poc2_name", "ntn", "stn"]

        widgets = {
            field: forms.TextInput(attrs={"class": "form-control text-uppercase"}) for field in text_fields
        }
        for field in uppercase_fields:
            widgets[field].attrs["data-uppercase"] = "1"
        widgets["name"].attrs["autofocus"] = "autofocus"
        widgets.update({
            "poc1_email": forms.EmailInput(attrs={"class": "form-control text-uppercase", "data-uppercase": "1"}),
            "poc2_email": forms.EmailInput(attrs={"class": "form-control text-uppercase", "data-uppercase": "1"}),
            "address": forms.Textarea(attrs={"class": "form-control text-uppercase", "rows": 3, "data-uppercase": "1"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        })


class TaxSettingsForm(forms.ModelForm):
    class Meta:
        model = TaxSettings
        percent_fields = ["sindh_percent", "punjab_percent", "ict_percent", "kpk_percent",
                          "balochistan_percent"]
        fields = percent_fields + ["provider_name", "provider_address", "provider_ntn", "provider_strn",
                                   "invoice_prefix", "payment_terms_days"]
        widgets = {
            field: forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0", "max": "100"})
            for field in percent_fields
        }
        widgets.update({
            "provider_name": forms.TextInput(attrs={"class": "form-control"}),
            "provider_address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "provider_ntn": forms.TextInput(attrs={"class": "form-control"}),
            "provider_strn": forms.TextInput(attrs={"class": "form-control"}),
            "invoice_prefix": forms.TextInput(attrs={"class": "form-control"}),
            "payment_terms_days": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
        })

################ EXPENSE & RATES ################
from django import forms
from .models import Expense
from operations.models import Trip

class ExpenseForm(forms.ModelForm):
    trip = forms.ModelChoiceField(
        queryset=Trip.objects.none(),
        empty_label="--- Select Trip ---",
        widget=forms.Select(attrs={'class': 'form-select', 'autofocus': 'autofocus'}),
    )

    class Meta:
        model = Expense
        # Hum 'total_expense' ko nikaal rahe hain kyunki ye auto-save hota hai
        exclude = ['total_expense'] 
        
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control datepicker'}),
            'trip': forms.Select(attrs={'class': 'form-select', 'autofocus': 'autofocus'}),
            'pump_name': forms.TextInput(attrs={'placeholder': 'Enter pump name'}),
            'slip_no': forms.TextInput(attrs={'placeholder': 'Slip # Optional'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['trip'].queryset = Trip.objects.select_related(
            'job__vehicle', 'route'
        ).order_by('-trip_date', '-id')
        self.fields['trip'].label_from_instance = lambda trip: (
            f"TRIP #{trip.trip_no or f'{trip.pk:06d}'} | {trip.route.route_code}"
        )
        
        # Baaki saari fields par loop chala kar bootstrap class add karna
        for name, field in self.fields.items():
            if name not in ['date', 'trip']: # Inke widgets humne upar de diye hain
                field.widget.attrs.update({"class": "form-control"})
            
            # Numeric fields mein default value 0 dikhane ke liye
            if isinstance(field, (forms.FloatField, forms.DecimalField)):
                field.widget.attrs.update({"step": "0.01"})

class ClientRateForm(forms.ModelForm):
    class Meta:
        model = ClientRate
        fields = [
            "sub_category", "rate_type", "route", "fuel_product", "current_fuel_price", "current_rate",
            "effective_percent", "updated_fuel_price", "weight_tons", "vehicle_type", "effective_date",
        ]
        widgets = {
            "sub_category": forms.Select(attrs={"class": "form-select"}),
            "rate_type": forms.Select(attrs={"class": "form-select"}),
            "route": forms.Select(attrs={
                "class": "form-select dropdown-search-select",
                "autofocus": "autofocus",
                "data-placeholder": "Type route code (e.g. KHI)...",
            }),
            "fuel_product": forms.Select(attrs={"class": "form-select"}),
            "current_fuel_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "current_rate": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "effective_percent": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "e.g. 50"}),
            "updated_fuel_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "weight_tons": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Tons"}),
            "vehicle_type": forms.Select(attrs={"class": "form-select"}),
            "effective_date": forms.DateInput(attrs={"class": "form-control datepicker"}),
        }

    def __init__(self, *args, client=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = client or getattr(self.instance, "client", None)
        self.fields["vehicle_type"].empty_label = "--- Select Type ---"
        self.fields["fuel_product"].empty_label = "--- Select Fuel Product ---"
        self.fields["sub_category"].empty_label = "--- Client default ---"
        self.fields["sub_category"].queryset = (
            ClientSubCategory.objects.filter(client=self.client) if self.client else ClientSubCategory.objects.none()
        )
        # Sub-Category / Rate Type only exist for clients flagged "Has
        # Sub-Categories" - for everyone else the form is exactly as before
        # (rate_type then stays AUTO, sub_category blank).
        if not (self.client and self.client.has_sub_categories):
            del self.fields["sub_category"]
            del self.fields["rate_type"]
        # The fuel-price fields aren't needed for a Fixed rate; for Auto they
        # are still required (checked in clean() below).
        for name in self.FUEL_FIELDS:
            self.fields[name].required = False
        self.fields["fuel_product"].queryset = FuelProduct.objects.all().order_by("name")

    FUEL_FIELDS = ("current_fuel_price", "effective_percent", "updated_fuel_price")

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("rate_type") == "FIXED":
            if cleaned.get("current_rate") is None:
                self.add_error("current_rate", "Enter the fixed rate.")
            for name in self.FUEL_FIELDS:
                cleaned[name] = Decimal(0)
        else:
            for name in self.FUEL_FIELDS + ("current_rate",):
                if cleaned.get(name) is None and name not in self.errors:
                    self.add_error(name, "This field is required.")
        route = cleaned.get("route")
        effective_date = cleaned.get("effective_date")
        if self.client and route and effective_date:
            dupes = ClientRate.objects.filter(
                client=self.client,
                sub_category=cleaned.get("sub_category"),
                route=route,
                fuel_product=cleaned.get("fuel_product"),
                vehicle_type=cleaned.get("vehicle_type"),
                weight_tons=cleaned.get("weight_tons"),
                effective_date=effective_date,
            )
            if self.instance.pk:
                dupes = dupes.exclude(pk=self.instance.pk)
            if dupes.exists():
                raise forms.ValidationError(
                    "A rate entry for this route, fuel product, vehicle type, and weight already "
                    "exists on this date - edit that entry instead of adding a duplicate."
                )
        return cleaned


class DedicatedRateForm(forms.ModelForm):
    class Meta:
        model = DedicatedRate
        fields = [
            "vehicle", "fixed_cost", "month", "fuel_avg", "fuel_price",
            "route", "distance_mode", "distance_km", "weight_tons", "vehicle_type", "effective_date",
        ]
        widgets = {
            "vehicle": forms.Select(attrs={
                "class": "form-select dropdown-search-select",
                "autofocus": "autofocus",
                "data-placeholder": "Type vehicle # ...",
            }),
            "fixed_cost": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "month": forms.DateInput(attrs={"class": "form-control datepicker"}),
            "fuel_avg": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Km/Ltr"}),
            "fuel_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "route": forms.Select(attrs={
                "class": "form-select dropdown-search-select",
                "data-placeholder": "Type route code (e.g. KHI)...",
            }),
            "distance_mode": forms.RadioSelect(),
            "distance_km": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "weight_tons": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Tons"}),
            "vehicle_type": forms.Select(attrs={"class": "form-select"}),
            "effective_date": forms.DateInput(attrs={"class": "form-control datepicker"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vehicle"].empty_label = "--- Select Vehicle ---"
        self.fields["vehicle"].label_from_instance = lambda obj: obj.vehicle_number
        self.fields["route"].empty_label = "--- Select Route ---"
        self.fields["vehicle_type"].empty_label = "--- Select Type ---"


from django import forms
from django.forms import inlineformset_factory
from .models import Vehicle, MaintenanceJob, MaintenancePart
from datetime import date


class MaintenanceJobForm(forms.ModelForm):
    class Meta:
        model = MaintenanceJob
        fields = [
            "vehicle", "date", "maintenance_type", "description",
            "odometer_km", "next_service_due_km",
            "spare_parts_vendor", "spare_parts_cost", "labor_cost",
            "status", "vendor_payment_status", "payment_date", "bill_ref",
            "unpaid_balance",
        ]
        widgets = {
            "vehicle": forms.Select(attrs={"class": "form-select", "autofocus": "autofocus"}),
            "date": forms.DateInput(attrs={
                "class": "form-control datepicker", "data-max-today": "1"
            }),
            "maintenance_type": forms.Select(attrs={"class": "form-select"}),
            "description": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Break Setting"}),
            "odometer_km": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "next_service_due_km": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "spare_parts_vendor": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. AMG"}),
            "spare_parts_cost": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "0.01"}),
            "labor_cost": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "0.01"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "vendor_payment_status": forms.Select(attrs={"class": "form-select"}),
            "payment_date": forms.DateInput(attrs={"class": "form-control datepicker"}),
            "bill_ref": forms.TextInput(attrs={"class": "form-control", "placeholder": "Bill / reference #"}),
            "unpaid_balance": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vehicle"].queryset = Vehicle.objects.filter(is_active=True).order_by("vehicle_number")
        self.fields["vehicle"].empty_label = "--- Choose Vehicle ---"


MaintenancePartFormSet = inlineformset_factory(
    MaintenanceJob,
    MaintenancePart,
    fields=["part_used", "quantity_used", "part_source", "inventory_item"],
    widgets={
        "part_used": forms.TextInput(attrs={"class": "form-control", "placeholder": "Part name"}),
        "quantity_used": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
        "part_source": forms.Select(attrs={"class": "form-select"}),
        "inventory_item": forms.Select(attrs={"class": "form-select"}),
    },
    extra=1,
    can_delete=True,
)


from .models import PartsInventory


class PartsInventoryForm(forms.ModelForm):
    class Meta:
        model = PartsInventory
        fields = ["part_name", "category", "stock_level", "reorder_point", "unit_cost"]
        widgets = {
            "part_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Break Oil Guard", "autofocus": "autofocus"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "stock_level": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "reorder_point": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "unit_cost": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "0.01"}),
        }