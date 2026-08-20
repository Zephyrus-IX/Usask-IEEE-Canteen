import csv

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView

from .forms import InventoryItemForm, LoadBalanceForm, NewSaleForm, RestockForm, StudentTabForm
from .models import BalanceTransaction, InventoryItem, RestockEvent, Sale, StudentTab
from .services import create_sale, load_student_balance, record_restock


def home(request):
    return render(request, "canteen/home.html")


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

    def get(self, request):
        return render(request, self.template_name, {"form": NewSaleForm()})

    def post(self, request):
        form = NewSaleForm(request.POST)
        if form.is_valid():
            try:
                sale = create_sale(
                    student_tab=form.cleaned_data["student_tab"],
                    items=form.cleaned_data["items"],
                    payment_method=form.cleaned_data["payment_method"],
                    handled_by=request.user,
                )
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                messages.success(request, f"Sale #{sale.pk} completed: ${sale.total_amount}")
                return redirect("new-sale")
        return render(request, self.template_name, {"form": form})


class LoadBalanceView(LoginRequiredMixin, View):
    template_name = "canteen/load_balance.html"

    def get(self, request):
        return render(request, self.template_name, {"form": LoadBalanceForm()})

    def post(self, request):
        form = LoadBalanceForm(request.POST)
        if form.is_valid():
            try:
                transaction = load_student_balance(
                    student_tab=form.cleaned_data["student_tab"],
                    amount=form.cleaned_data["amount"],
                    payment_method=form.cleaned_data["payment_method"],
                    handled_by=request.user,
                    note=form.cleaned_data["note"],
                )
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                messages.success(request, f"Loaded ${transaction.amount} onto {transaction.student_tab}")
                return redirect("load-balance")
        return render(request, self.template_name, {"form": form})


class RestockCreateView(LoginRequiredMixin, View):
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


class ReportsView(LoginRequiredMixin, TemplateView):
    template_name = "canteen/reports.html"


class ExportSalesCsvView(LoginRequiredMixin, View):
    def get(self, request):
        sales = Sale.objects.select_related("student_tab").order_by("created_at")
        rows = (
            [
                sale.id,
                sale.created_at.isoformat(),
                sale.student_tab.student_id,
                f"{sale.student_tab.first_name} {sale.student_tab.last_name}",
                sale.payment_method,
                sale.status,
                sale.total_amount,
            ]
            for sale in sales
        )
        return csv_response(
            "sales.csv",
            ["sale_id", "created_at", "student_id", "student_name", "payment_method", "status", "total_amount"],
            rows,
        )


class ExportBalanceLoadsCsvView(LoginRequiredMixin, View):
    def get(self, request):
        transactions = BalanceTransaction.objects.select_related("student_tab").filter(
            transaction_type=BalanceTransaction.TransactionType.LOAD
        ).order_by("created_at")
        rows = (
            [
                transaction.id,
                transaction.created_at.isoformat(),
                transaction.student_tab.student_id,
                f"{transaction.student_tab.first_name} {transaction.student_tab.last_name}",
                transaction.payment_method,
                transaction.amount,
                transaction.note,
            ]
            for transaction in transactions
        )
        return csv_response(
            "balance-loads.csv",
            ["transaction_id", "created_at", "student_id", "student_name", "payment_method", "amount", "note"],
            rows,
        )


class ExportRestocksCsvView(LoginRequiredMixin, View):
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


class ExportInventoryCsvView(LoginRequiredMixin, View):
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


class ExportStudentTabsCsvView(LoginRequiredMixin, View):
    def get(self, request):
        tabs = StudentTab.objects.order_by("student_id")
        rows = (
            [
                tab.student_id,
                tab.first_name,
                tab.last_name,
                tab.is_active,
                tab.is_ieee_member,
                tab.ieee_member_id,
                tab.ieee_membership_expires_on,
                tab.current_balance,
            ]
            for tab in tabs
        )
        return csv_response(
            "student-tabs.csv",
            [
                "student_id",
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


class StudentTabListView(LoginRequiredMixin, ListView):
    model = StudentTab
    template_name = "canteen/student_tab_list.html"
    context_object_name = "student_tabs"
    paginate_by = 50


class StudentTabCreateView(LoginRequiredMixin, CreateView):
    model = StudentTab
    form_class = StudentTabForm
    template_name = "canteen/student_tab_form.html"
    success_url = reverse_lazy("student-tab-list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class InventoryItemListView(LoginRequiredMixin, ListView):
    model = InventoryItem
    template_name = "canteen/inventory_item_list.html"
    context_object_name = "inventory_items"
    paginate_by = 50


class InventoryItemCreateView(LoginRequiredMixin, CreateView):
    model = InventoryItem
    form_class = InventoryItemForm
    template_name = "canteen/inventory_item_form.html"
    success_url = reverse_lazy("inventory-item-list")
