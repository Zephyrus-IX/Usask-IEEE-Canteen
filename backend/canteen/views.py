import csv

from axes.utils import reset as reset_login_attempts
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from .credentials import generate_temporary_password
from .forms import (
    AccountForm,
    InventoryItemForm,
    LoadBalanceForm,
    NewSaleForm,
    RequiredPasswordChangeForm,
    RestockForm,
)
from .models import Account, BalanceTransaction, InventoryItem, RestockEvent, Sale
from .services import create_sale, load_student_balance, record_restock


def is_staff_user(user) -> bool:
    return bool(user.is_authenticated and user.is_staff)


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return is_staff_user(self.request.user)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied
        return super().handle_no_permission()


def get_user_account(user):
    try:
        return user.canteen_account
    except Account.DoesNotExist:
        return None


def cheapest_available_item_price_for(account):
    prices = [
        item.price_for_account(account)
        for item in InventoryItem.objects.filter(is_active=True, quantity_on_hand__gt=0)
    ]
    return min(prices) if prices else None


def new_sale_context(form, request, account):
    cheapest_item_price = cheapest_available_item_price_for(account) if account else None
    balance_warning = bool(
        account
        and cheapest_item_price is not None
        and account.current_balance < cheapest_item_price
    )
    return {
        "form": form,
        "account": account,
        "uses_balance_only": True,
        "is_staff_user": is_staff_user(request.user),
        "cheapest_item_price": cheapest_item_price,
        "balance_warning": balance_warning,
    }


def home(request):
    return render(request, "canteen/home.html", {"is_staff_user": is_staff_user(request.user)})


def csv_response(filename: str, headers: list[str], rows):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return response


class NewSaleView(LoginRequiredMixin, View):
    template_name = "canteen/new_sale.html"

    def get_account_for_request(self, request, form=None):
        if is_staff_user(request.user):
            return form.cleaned_data["account"] if form and form.is_valid() else None
        account = get_user_account(request.user)
        if not account:
            raise ValidationError("No canteen account is linked to your login. Contact the IEEE vice-chair for help.")
        return account

    def get(self, request):
        account = None if is_staff_user(request.user) else get_user_account(request.user)
        form = NewSaleForm(staff_user=is_staff_user(request.user))
        return render(request, self.template_name, new_sale_context(form, request, account))

    def post(self, request):
        form = NewSaleForm(request.POST, staff_user=is_staff_user(request.user))
        account = None
        if form.is_valid():
            try:
                account = form.cleaned_data["account"] if is_staff_user(request.user) else get_user_account(request.user)
                if account is None:
                    raise ValidationError("No canteen account is linked to your login. Contact the IEEE vice-chair for help.")
                sale = create_sale(
                    account=account,
                    items=form.cleaned_data["items"],
                    payment_method=Sale.PaymentMethod.BALANCE,
                    handled_by=request.user,
                )
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                messages.success(request, f"Sale #{sale.pk} completed: ${sale.total_amount}. Remaining balance: ${account.current_balance}")
                return redirect("new-sale")
        if not is_staff_user(request.user):
            account = get_user_account(request.user)
        return render(request, self.template_name, new_sale_context(form, request, account))


class AccountDetailView(LoginRequiredMixin, DetailView):
    model = Account
    template_name = "canteen/account_detail.html"
    context_object_name = "account"

    def get_object(self, queryset=None):
        if is_staff_user(self.request.user) and "pk" in self.kwargs:
            return super().get_object(queryset)
        account = get_user_account(self.request.user)
        if not account:
            raise PermissionDenied("No canteen account is linked to your login.")
        return account

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = context["account"]
        context["balance_transactions"] = account.balance_transactions.select_related("related_sale")[:50]
        context["sales"] = account.sales.prefetch_related("items__inventory_item")[:50]
        return context


@method_decorator(never_cache, name="dispatch")
class RequiredPasswordChangeView(LoginRequiredMixin, View):
    template_name = "canteen/set_password.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            account = get_user_account(request.user)
            if request.user.is_staff or account is None or not account.must_change_password:
                raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, self.template_name, {"form": RequiredPasswordChangeForm(request.user)})

    def post(self, request):
        form = RequiredPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            account = get_user_account(user)
            if account:
                account.must_change_password = False
                account.save(update_fields=["must_change_password"])
            update_session_auth_hash(request, user)
            messages.success(request, "Your password has been created.")
            return redirect("home")
        return render(request, self.template_name, {"form": form})


class LoadBalanceView(StaffRequiredMixin, LoginRequiredMixin, View):
    template_name = "canteen/load_balance.html"

    def get(self, request):
        return render(request, self.template_name, {"form": LoadBalanceForm()})

    def post(self, request):
        form = LoadBalanceForm(request.POST)
        if form.is_valid():
            try:
                transaction = load_student_balance(
                    account=form.cleaned_data["account"],
                    amount=form.cleaned_data["amount"],
                    payment_method=form.cleaned_data["payment_method"],
                    handled_by=request.user,
                    note=form.cleaned_data["note"],
                )
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                messages.success(request, f"Loaded ${transaction.amount} onto {transaction.account}")
                return redirect("load-balance")
        return render(request, self.template_name, {"form": form})


class RestockCreateView(StaffRequiredMixin, LoginRequiredMixin, View):
    template_name = "canteen/restock_form.html"

    def get(self, request):
        return render(request, self.template_name, {"form": RestockForm()})

    def post(self, request):
        form = RestockForm(request.POST)
        if form.is_valid():
            try:
                restock = record_restock(
                    vendor=form.cleaned_data["vendor"],
                    items=form.cleaned_data["items"],
                    tax_rates=list(form.cleaned_data["tax_rates"]),
                    entered_by=request.user,
                    notes=form.cleaned_data["notes"],
                )
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                messages.success(request, f"Restock #{restock.pk} recorded: ${restock.total_paid}")
                return redirect("restock-create")
        return render(request, self.template_name, {"form": form})


class ReportsView(StaffRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "canteen/reports.html"


class ExportSalesCsvView(StaffRequiredMixin, LoginRequiredMixin, View):
    def get(self, request):
        sales = Sale.objects.select_related("account__user").order_by("created_at")
        rows = (
            [
                sale.id,
                sale.created_at.isoformat(),
                sale.account.user.username if sale.account.user_id else "",
                f"{sale.account.first_name} {sale.account.last_name}",
                sale.payment_method,
                sale.status,
                sale.total_amount,
            ]
            for sale in sales
        )
        return csv_response(
            "sales.csv",
            ["sale_id", "created_at", "nsid", "student_name", "payment_method", "status", "total_amount"],
            rows,
        )


class ExportBalanceLoadsCsvView(StaffRequiredMixin, LoginRequiredMixin, View):
    def get(self, request):
        transactions = BalanceTransaction.objects.select_related("account__user").filter(
            transaction_type=BalanceTransaction.TransactionType.LOAD
        ).order_by("created_at")
        rows = (
            [
                transaction.id,
                transaction.created_at.isoformat(),
                transaction.account.user.username if transaction.account.user_id else "",
                f"{transaction.account.first_name} {transaction.account.last_name}",
                transaction.payment_method,
                transaction.amount,
                transaction.note,
            ]
            for transaction in transactions
        )
        return csv_response(
            "balance-loads.csv",
            ["transaction_id", "created_at", "nsid", "student_name", "payment_method", "amount", "note"],
            rows,
        )


class ExportRestocksCsvView(StaffRequiredMixin, LoginRequiredMixin, View):
    def get(self, request):
        restocks = RestockEvent.objects.order_by("restocked_on", "created_at")
        rows = (
            [restock.id, restock.restocked_on, restock.vendor, restock.subtotal, restock.total_tax, restock.total_paid]
            for restock in restocks
        )
        return csv_response(
            "restocks.csv",
            ["restock_id", "restocked_on", "vendor", "subtotal", "total_tax", "total_paid"],
            rows,
        )


class ExportInventoryCsvView(StaffRequiredMixin, LoginRequiredMixin, View):
    def get(self, request):
        items = InventoryItem.objects.order_by("name")
        rows = (
            [
                item.name,
                item.quantity_on_hand,
                item.member_price,
                item.non_member_price,
                item.low_stock_threshold,
                item.is_active,
            ]
            for item in items
        )
        return csv_response(
            "inventory.csv",
            ["name", "quantity_on_hand", "member_price", "non_member_price", "low_stock_threshold", "is_active"],
            rows,
        )


class ExportAccountsCsvView(StaffRequiredMixin, LoginRequiredMixin, View):
    def get(self, request):
        accounts = Account.objects.select_related("user").order_by("user__username")
        rows = (
            [
                account.user.username if account.user_id else "",
                account.first_name,
                account.last_name,
                account.is_active,
                account.is_ieee_member,
                account.ieee_member_id,
                account.ieee_membership_expires_on,
                account.current_balance,
            ]
            for account in accounts
        )
        return csv_response(
            "accounts.csv",
            [
                "nsid",
                "first_name",
                "last_name",
                "is_active",
                "is_ieee_member",
                "ieee_member_id",
                "ieee_membership_expires_on",
                "current_balance",
            ],
            rows,
        )


class AccountListView(StaffRequiredMixin, LoginRequiredMixin, ListView):
    model = Account
    template_name = "canteen/account_list.html"
    context_object_name = "accounts"
    paginate_by = 50


class AccountCreateView(StaffRequiredMixin, LoginRequiredMixin, CreateView):
    model = Account
    form_class = AccountForm
    template_name = "canteen/account_form.html"
    success_url = reverse_lazy("account-list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        with transaction.atomic():
            self.object = form.save()
            reset_login_attempts(username=self.object.user.username)
        response = render(
            self.request,
            "canteen/temporary_password.html",
            {"account": self.object, "temporary_password": form.temporary_password, "was_reset": False},
        )
        response["Cache-Control"] = "max-age=0, no-cache, no-store, must-revalidate, private"
        return response


@method_decorator(never_cache, name="dispatch")
class AccountResetPasswordView(StaffRequiredMixin, LoginRequiredMixin, View):
    def post(self, request, pk):
        account = get_object_or_404(Account.objects.select_related("user"), pk=pk)
        if not account.user_id:
            raise PermissionDenied("Only linked customer accounts can receive temporary passwords.")
        if account.user.is_staff or account.user.is_superuser:
            raise PermissionDenied("Executive credentials cannot be reset from a customer account.")
        temporary_password = generate_temporary_password()
        with transaction.atomic():
            account.user.set_password(temporary_password)
            account.user.save(update_fields=["password"])
            account.must_change_password = True
            account.save(update_fields=["must_change_password"])
            reset_login_attempts(username=account.user.username)
        response = render(
            request,
            "canteen/temporary_password.html",
            {"account": account, "temporary_password": temporary_password, "was_reset": True},
        )
        response["Cache-Control"] = "max-age=0, no-cache, no-store, must-revalidate, private"
        return response


class InventoryItemListView(LoginRequiredMixin, ListView):
    model = InventoryItem
    template_name = "canteen/inventory_item_list.html"
    context_object_name = "inventory_items"
    paginate_by = 50


class InventoryItemCreateView(StaffRequiredMixin, LoginRequiredMixin, CreateView):
    model = InventoryItem
    form_class = InventoryItemForm
    template_name = "canteen/inventory_item_form.html"
    success_url = reverse_lazy("inventory-item-list")
