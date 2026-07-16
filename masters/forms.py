from django import forms
from .models import Vehicle, Driver, Vendor, City, Route, Client, Expense, ClientRate, DriverSalary
from operations.models import Trip

################ VEHICLES ################

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = "__all__"
        
        # 1. Purani driver fields ko list se nikaal diya, ab sirf 'driver' dropdown bacha hai
        text_fields = [
            "vehicle_number", "engine_no", "chassis_no", "container_no", 
            "color", "current_location", "current_km"
        ]
        
        date_fields = [
            "sindh_permit_expiry", "punjab_permit_expiry", "kpk_permit_expiry", 
            "balochistan_permit_expiry", "fitness_expiry_sindh", "fitness_expiry_punjab", 
            "fitness_expiry_kpk", "fitness_expiry_balochistan", "last_meter_update"
        ]

        # 2. Base widgets for text fields
        widgets = {
            field: forms.TextInput(attrs={"class": "form-control"}) for field in text_fields
        }
        
        # 3. Date fields widgets
        widgets.update({
            field: forms.DateInput(attrs={"class": "form-control", "type": "date"}) for field in date_fields
        })
        
        # 4. Dropdowns (is mein ab 'driver' bhi shamil hai)
        widgets.update({
            "vendor": forms.Select(attrs={"class": "form-select"}),
            "driver": forms.Select(attrs={"class": "form-select"}), # Naya Driver Dropdown
            "vehicle_mode": forms.Select(attrs={"class": "form-select"}),
            "vehicle_type": forms.Select(attrs={"class": "form-select"}),
            "wheeler": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        })

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
        self.fields["cnic_expiry"].widget = forms.DateInput(attrs={"class": "form-control", "type": "date"})
        self.fields["license_expiry"].widget = forms.DateInput(attrs={"class": "form-control", "type": "date"})
        self.fields["joining_date"].widget = forms.DateInput(attrs={"class": "form-control", "type": "date"})
        self.fields["is_active"].widget.attrs.update({"class": "form-check-input"})

################ SALARY ################

class DriverSalaryForm(forms.ModelForm):
    class Meta:
        model = DriverSalary
        fields = "__all__"
        widgets = {
            "driver": forms.Select(attrs={"class": "form-select"}),
            "month": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "salary_amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
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
            "origin": forms.Select(attrs={"class": "form-select"}),
            "destination": forms.Select(attrs={"class": "form-select"}),
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
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
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
            "route": forms.Select(attrs={"class": "form-select"}),
            "rate": forms.NumberInput(attrs={"class": "form-control"}),
            "fuel_price": forms.NumberInput(attrs={"class": "form-control"}),
            "effective_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }

from django import forms
from .models import Vehicle, VehicleMaintenance
from datetime import date

class MaintenanceForm(forms.ModelForm):
    class Meta:
        model = VehicleMaintenance
        # Aapke model ke asli variables:
        fields = ["vehicle", "maintenance_type", "change_date", "change_km", "remarks"]
        
        widgets = {
            "vehicle": forms.Select(attrs={
                "class": "form-select border-primary",
                "style": "display: block !important; width: 100%;"
            }),
            "maintenance_type": forms.Select(attrs={
                "class": "form-select"
            }),
            "change_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
                "max": date.today().isoformat()
            }),
            "change_km": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter KM Reading (e.g. 45000)",
                "min": "0"
            }),
            "remarks": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Optional maintenance details..."
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Labels ko model variables ke sath map kiya:
        self.fields['vehicle'].label = "Select Vehicle"
        self.fields['maintenance_type'].label = "Type of Service"
        self.fields['change_date'].label = "Service Date"
        self.fields['change_km'].label = "Odometer Reading (KM)"
        self.fields['remarks'].label = "Additional Notes"
        
        self.fields['vehicle'].queryset = Vehicle.objects.filter(is_active=True).order_by('vehicle_number')
        self.fields['vehicle'].empty_label = "--- Choose Vehicle ---"