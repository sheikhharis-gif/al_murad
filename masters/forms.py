from django import forms
from .models import (
    Vehicle, VehicleType, Wheeler, VehicleTyre, Driver, Vendor,
    City, Route, Client, Expense, ClientRate, DriverSalary
)
from operations.models import Trip

################ VEHICLES ################

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = "__all__"

        # 1. Purani driver fields ko list se nikaal diya, ab sirf 'driver' dropdown bacha hai
        text_fields = [
            "vehicle_number", "engine_no", "chassis_no", "container_no",
            "color", "current_km", "make", "registration_name",
        ]

        date_fields = [
            "sindh_permit_expiry", "punjab_permit_expiry", "kpk_permit_expiry",
            "balochistan_permit_expiry", "fitness_expiry_sindh", "fitness_expiry_punjab",
            "fitness_expiry_kpk", "fitness_expiry_balochistan", "last_meter_update",
            "purchase_date",
        ]

        # 2. Base widgets for text fields
        widgets = {
            field: forms.TextInput(attrs={"class": "form-control"}) for field in text_fields
        }

        # 3. Date fields widgets
        widgets.update({
            field: forms.DateInput(attrs={"class": "form-control datepicker"}) for field in date_fields
        })

        # 4. Dropdowns (is mein ab 'driver' bhi shamil hai)
        widgets.update({
            "vendor": forms.Select(attrs={"class": "form-select"}),
            "driver": forms.Select(attrs={"class": "form-select searchable-select"}), # Naya Driver Dropdown
            "vehicle_mode": forms.Select(attrs={"class": "form-select"}),
            "vehicle_type": forms.Select(attrs={"class": "form-select"}),
            "wheeler": forms.Select(attrs={"class": "form-select"}),
            "current_location": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "leased": forms.Select(attrs={"class": "form-select"}, choices=((False, "No"), (True, "Yes"))),
            "model_year": forms.NumberInput(attrs={"class": "form-control", "placeholder": "e.g. 2014"}),
            "value": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active drivers when assigning one to a vehicle, A-Z (Driver.Meta.ordering).
        active_drivers = Driver.objects.filter(is_active=True)
        if self.instance and self.instance.pk and self.instance.driver_id:
            # Keep the currently assigned driver selectable even if they've since gone inactive.
            active_drivers = active_drivers | Driver.objects.filter(pk=self.instance.driver_id)
        self.fields["driver"].queryset = active_drivers.distinct()
        self.fields["driver"].empty_label = "--- No Driver Assigned ---"

        self.fields["vendor"].empty_label = "--- No Vendor ---"
        self.fields["vehicle_type"].empty_label = "--- Select Type ---"
        self.fields["wheeler"].empty_label = "--- Select Wheeler ---"
        self.fields["current_location"].empty_label = "--- Select City ---"


VehicleTyreFormSet = forms.inlineformset_factory(
    Vehicle,
    VehicleTyre,
    fields=["tyre_number", "installed_date"],
    widgets={
        "tyre_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Tyre number"}),
        "installed_date": forms.DateInput(attrs={"class": "form-control datepicker"}),
    },
    extra=1,
    can_delete=True,
)


class VehicleTypeForm(forms.ModelForm):
    class Meta:
        model = VehicleType
        fields = ["name"]
        widgets = {"name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 20FT DRY"})}

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

class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = "__all__"
        widgets = {
            field: forms.TextInput(attrs={"class": "form-control"})
            for field in [
                "name", "father_name", "mobile", "cnic",
                "license_number", "reference1_name",
                "reference1_mobile", "reference2_name",
                "reference2_mobile"
            ]
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["address"].widget = forms.Textarea(attrs={"class": "form-control", "rows": 3})
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
            "driver": forms.Select(attrs={"class": "form-select"}),
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

################ VENDOR & CLIENT ################

class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = "__all__"
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "poc": forms.TextInput(attrs={"class": "form-control"}),
            "ntn": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = "__all__"
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "poc": forms.TextInput(attrs={"class": "form-control"}),
            "ntn": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "billing_company": forms.TextInput(attrs={"class": "form-control"}),
        }

################ EXPENSE & RATES ################
from django import forms
from .models import Expense
from operations.models import Trip

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        # Hum 'total_expense' ko nikaal rahe hain kyunki ye auto-save hota hai
        exclude = ['total_expense'] 
        
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control datepicker'}),
            'trip': forms.Select(attrs={'class': 'form-select'}),
            'pump_name': forms.TextInput(attrs={'placeholder': 'Enter pump name'}),
            'slip_no': forms.TextInput(attrs={'placeholder': 'Slip # Optional'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
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
        fields = ["route", "rate", "fuel_price", "effective_date"]
        widgets = {
            "route": forms.Select(attrs={"class": "form-select searchable-select"}),
            "rate": forms.NumberInput(attrs={"class": "form-control"}),
            "fuel_price": forms.NumberInput(attrs={"class": "form-control"}),
            "effective_date": forms.DateInput(attrs={"class": "form-control datepicker"}),
        }

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
            "vehicle": forms.Select(attrs={"class": "form-select"}),
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
            "part_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Break Oil Guard"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "stock_level": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "reorder_point": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "unit_cost": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "0.01"}),
        }