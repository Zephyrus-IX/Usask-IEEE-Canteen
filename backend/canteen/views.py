from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView

from .forms import InventoryItemForm, NewSaleForm, StudentTabForm
from .models import InventoryItem, StudentTab
from .services import create_sale


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
                    items=[
                        {
                            "inventory_item": form.cleaned_data["item"],
                            "quantity": form.cleaned_data["quantity"],
                        }
                    ],
                    payment_method=form.cleaned_data["payment_method"],
                    handled_by=request.user,
                )
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                messages.success(request, f"Sale #{sale.pk} completed: ${sale.total_amount}")
                return redirect("new-sale")
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
