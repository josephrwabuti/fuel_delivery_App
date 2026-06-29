from django import forms
from .models import Order

class OrderForm(forms.ModelForm):

    class Meta:
        model = Order

        fields = [
            "station",
            "fuel_type",
            "quantity",
            "delivery_address",
            "phone",
            "notes",
        ]

        widgets = {
            "delivery_address": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }