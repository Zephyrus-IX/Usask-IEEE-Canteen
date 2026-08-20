from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from .forms import InventoryItemForm, StudentTabForm
from .models import InventoryItem, StudentTab


def home(request):
    return render(request, "canteen/home.html")


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
