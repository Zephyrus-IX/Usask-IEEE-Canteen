from django.contrib import admin
from django.urls import include, path

from canteen import views

urlpatterns = [
    path("", views.home, name="home"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("sales/new/", views.NewSaleView.as_view(), name="new-sale"),
    path("accounts/load-balance/", views.LoadBalanceView.as_view(), name="load-balance"),
    path("restocks/new/", views.RestockCreateView.as_view(), name="restock-create"),
    path("reports/", views.ReportsView.as_view(), name="reports"),
    path("reports/sales.csv", views.ExportSalesCsvView.as_view(), name="export-sales-csv"),
    path("reports/balance-loads.csv", views.ExportBalanceLoadsCsvView.as_view(), name="export-balance-loads-csv"),
    path("reports/restocks.csv", views.ExportRestocksCsvView.as_view(), name="export-restocks-csv"),
    path("reports/inventory.csv", views.ExportInventoryCsvView.as_view(), name="export-inventory-csv"),
    path("reports/accounts.csv", views.ExportAccountsCsvView.as_view(), name="export-accounts-csv"),
    path("accounts/me/", views.AccountDetailView.as_view(), name="account-detail"),
    path("accounts/<int:pk>/", views.AccountDetailView.as_view(), name="account-detail-staff"),
    path("accounts/", views.AccountListView.as_view(), name="account-list"),
    path("accounts/new/", views.AccountCreateView.as_view(), name="account-create"),
    path("inventory/", views.InventoryItemListView.as_view(), name="inventory-item-list"),
    path("inventory/new/", views.InventoryItemCreateView.as_view(), name="inventory-item-create"),
    path("admin/", admin.site.urls),
]
