from django import forms

from .models import InventoryItem, StudentTab


class StudentTabForm(forms.ModelForm):
    class Meta:
        model = StudentTab
        fields = [
            "student_id",
            "first_name",
            "last_name",
            "is_active",
            "is_ieee_member",
            "ieee_member_id",
            "ieee_membership_expires_on",
            "notes",
        ]
        widgets = {
            "ieee_membership_expires_on": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = [
            "name",
            "quantity_on_hand",
            "member_price",
            "non_member_price",
            "low_stock_threshold",
            "is_active",
            "notes",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
