from django import forms
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User

from .credentials import generate_temporary_password
from .models import Account, BalanceTransaction, InventoryItem, TaxRate

SALE_ITEM_ROW_COUNT = 5
RESTOCK_ITEM_ROW_COUNT = 5


class AccountForm(forms.ModelForm):
    nsid = forms.CharField(label="NSID", max_length=150)

    class Meta:
        model = Account
        fields = [
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order_fields([
            "nsid",
            "first_name",
            "last_name",
            "is_active",
            "is_ieee_member",
            "ieee_member_id",
            "ieee_membership_expires_on",
            "notes",
        ])
        if self.instance and self.instance.user_id:
            self.fields["nsid"].initial = self.instance.user.username

    def clean_nsid(self):
        nsid = self.cleaned_data["nsid"].strip().lower()
        user_qs = User.objects.filter(username__iexact=nsid)
        if self.instance and self.instance.user_id:
            user_qs = user_qs.exclude(pk=self.instance.user_id)
        if user_qs.exists():
            raise forms.ValidationError("An account already uses this NSID.")
        return nsid

    def save(self, commit=True):
        account = super().save(commit=False)
        nsid = self.cleaned_data["nsid"]
        if account.user_id:
            user = account.user
            user.username = nsid
        else:
            user = User(username=nsid, first_name=account.first_name, last_name=account.last_name)
            self.temporary_password = generate_temporary_password()
            user.set_password(self.temporary_password)
            account.must_change_password = True
        user.first_name = account.first_name
        user.last_name = account.last_name
        if commit:
            user.save()
            account.user = user
            account.save()
            self.save_m2m()
        else:
            account.user = user
        return account


class RequiredPasswordChangeForm(SetPasswordForm):
    pass


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
    account = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        label="Account",
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
        self.fields["account"].queryset = Account.objects.filter(is_active=True).order_by("user__username")


class NewSaleForm(forms.Form):
    account = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        label="Account",
        required=False,
    )

    def __init__(self, *args, staff_user=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.staff_user = staff_user
        if staff_user:
            self.fields["account"].required = True
            self.fields["account"].queryset = Account.objects.filter(is_active=True).order_by("user__username")
        else:
            self.fields.pop("account")
        item_queryset = InventoryItem.objects.filter(is_active=True, quantity_on_hand__gt=0).order_by("name")
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


class RestockForm(forms.Form):
    vendor = forms.CharField(required=False, max_length=120)
    tax_rates = forms.ModelMultipleChoiceField(
        queryset=TaxRate.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Taxes applied",
    )
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tax_rates"].queryset = TaxRate.objects.filter(is_active=True).order_by("name")
        item_queryset = InventoryItem.objects.filter(is_active=True).order_by("name")
        for row_number in range(1, RESTOCK_ITEM_ROW_COUNT + 1):
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
            self.fields[f"line_subtotal_{row_number}"] = forms.DecimalField(
                min_value=0.01,
                max_digits=10,
                decimal_places=2,
                label="Pre-tax subtotal",
                required=False,
            )

    @property
    def item_rows(self):
        return [
            (
                self[f"item_{row_number}"],
                self[f"quantity_{row_number}"],
                self[f"line_subtotal_{row_number}"],
            )
            for row_number in range(1, RESTOCK_ITEM_ROW_COUNT + 1)
        ]

    def clean(self):
        cleaned_data = super().clean()
        items = []
        for row_number in range(1, RESTOCK_ITEM_ROW_COUNT + 1):
            item = cleaned_data.get(f"item_{row_number}")
            quantity = cleaned_data.get(f"quantity_{row_number}")
            line_subtotal = cleaned_data.get(f"line_subtotal_{row_number}")
            row_has_any_data = item or quantity or line_subtotal
            row_has_all_data = item and quantity and line_subtotal
            if row_has_any_data and not row_has_all_data:
                if not item:
                    self.add_error(f"item_{row_number}", "Select an item for this row.")
                if not quantity:
                    self.add_error(f"quantity_{row_number}", "Enter a quantity for this row.")
                if not line_subtotal:
                    self.add_error(f"line_subtotal_{row_number}", "Enter the pre-tax subtotal for this row.")
            elif row_has_all_data:
                items.append(
                    {
                        "inventory_item": item,
                        "quantity": quantity,
                        "line_subtotal": line_subtotal,
                    }
                )
        if not items:
            raise forms.ValidationError("Restock must contain at least one item.")
        cleaned_data["items"] = items
        return cleaned_data
