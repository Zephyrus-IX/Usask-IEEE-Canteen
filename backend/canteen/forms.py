from django import forms

from .models import InventoryItem, Sale, StudentTab


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


class NewSaleForm(forms.Form):
    student_tab = forms.ModelChoiceField(
        queryset=StudentTab.objects.none(),
        label="Student tab",
    )
    item = forms.ModelChoiceField(
        queryset=InventoryItem.objects.none(),
        label="Item",
    )
    quantity = forms.IntegerField(min_value=1, initial=1)
    payment_method = forms.ChoiceField(choices=Sale.PaymentMethod.choices)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["student_tab"].queryset = StudentTab.objects.filter(is_active=True).order_by(
            "student_id"
        )
        self.fields["item"].queryset = InventoryItem.objects.filter(
            is_active=True, quantity_on_hand__gt=0
        ).order_by("name")
