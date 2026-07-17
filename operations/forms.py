from django import forms
from django.apps import apps
from .models import Trip, Job

# -----------------------
# JOB FORM
# -----------------------
class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        # Sirf wahi fields rakhein jo ab Model mein mojud hain
        fields = [
            "vehicle", 
            "remarks",
        ]

        widgets = {
            "vehicle": forms.Select(attrs={"class": "form-control"}),
            "remarks": forms.Textarea(attrs={
                "class": "form-control", 
                "rows": 3,
                "placeholder": "Voyage details..."
            }),
        }

from django import forms
from django.apps import apps

class TripForm(forms.ModelForm):
    # Sirf wahi fields rakhen jo user ne enter karni hain
    job = forms.ModelChoiceField(
        queryset=None, 
        label="Select Active Job",
        widget=forms.Select(attrs={"class": "form-control"})
    )
    client = forms.ModelChoiceField(
        queryset=None, 
        widget=forms.Select(attrs={"class": "form-control"})
    )
    route = forms.ModelChoiceField(
        queryset=None, 
        widget=forms.Select(attrs={"class": "form-control"})
    )

    class Meta:
        model = apps.get_model("operations", "Trip")
        # In fields mein se vehicle aur driver nikal diye gaye hain
        fields = [
            "job", "client", "trip_date", "route",
            "bilty_number", "weight", "rate", "detention",
        ]
        widgets = {
            "trip_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "bilty_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Bilty No."}),
            "weight": forms.NumberInput(attrs={"class": "form-control", "placeholder": "0.00"}),
            "rate": forms.NumberInput(attrs={"class": "form-control", "placeholder": "0.00"}),
            "detention": forms.NumberInput(attrs={"class": "form-control", "placeholder": "0.00"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Models dynamically get karna
        JobModel = apps.get_model("operations", "Job")
        ClientModel = apps.get_model("masters", "Client")
        RouteModel = apps.get_model("masters", "Route")

        # Logic: Sirf wo Jobs dikhayen jo abhi 'Active' hain (taake purani jobs par trips na dalen)
        self.fields["job"].queryset = JobModel.objects.all()
        self.fields["client"].queryset = ClientModel.objects.all()
        self.fields["route"].queryset = RouteModel.objects.all()