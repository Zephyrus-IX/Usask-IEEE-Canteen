from django import forms

from .models import BalanceTransaction, InventoryItem, Sale, StudentTab

SALE_ITEM_ROW_COUNT = 5


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


class LoadBalanceForm(forms.Form):
    student_tab = forms.ModelChoiceField(
        queryset=StudentTab.objects.none(),
        label="Student tab",
    )
    amount = forms.DecimalField(min_value=0.01, max_digits=10, decimal_places=2)
    payment_method = forms.ChoiceField(
        choices=(
            (BalanceTransaction.PaymentMethod.CASH, "Cash"),
            (BalanceTransaction.PaymentMethod.CARD, "Card"),
        )
    )
    note = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["student_tab"].queryset = StudentTab.objects.filter(is_active=True).order_by(
            "student_id"
        )


class NewSaleForm(forms.Form):
    student_tab = forms.ModelChoiceField(
        queryset=StudentTab.objects.none(),
        label="Student tab",
    )
    payment_method = forms.ChoiceField(choices=Sale.PaymentMethod.choices)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["student_tab"].queryset = StudentTab.objects.filter(is_active=True).order_by(
            "student_id"
        )
        item_queryset = InventoryItem.objects.filter(is_active=True, quantity_on_hand__gt=0).order_by(
            "name"
        )
        for row_number in range(1, SALE_ITEM_ROW_COUNT + 1):
            self.fields[f"item_{row_number}"] = forms.ModelChoiceField(
                queryset=item_queryset,
                label=f"Item {row_number}",
                required=False,
            )
            self.fields[f"quantity_{row_number}"] = forms.IntegerField(
                min_value=1,
                label="Qty",
                required=False,
            )

    @property
    def item_rows(self):
        return [
            (self[f"item_{row_number}"], self[f"quantity_{row_number}"])
            for row_number in range(1, SALE_ITEM_ROW_COUNT + 1)
        ]

    def clean(self):
        cleaned_data = super().clean()
        items = []
        for row_number in range(1, SALE_ITEM_ROW_COUNT + 1):
            item = cleaned_data.get(f"item_{row_number}")
            quantity = cleaned_data.get(f"quantity_{row_number}")
            if item and not quantity:
                self.add_error(f"quantity_{row_number}", "Enter a quantity for this item.")
            elif quantity and not item:
                self.add_error(f"item_{row_number}", "Select an item for this quantity.")
            elif item and quantity:
                items.append({"inventory_item": item, "quantity": quantity})
        if not items:
            raise forms.ValidationError("Sale must contain at least one item.")
        cleaned_data["items"] = items
        return cleaned_data
