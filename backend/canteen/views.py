from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView

from .forms import InventoryItemForm, LoadBalanceForm, NewSaleForm, RestockForm, StudentTabForm
from .models import InventoryItem, StudentTab
from .services import create_sale, load_student_balance, record_restock


def home(request):
    return render(request, "canteen/home.html")


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
