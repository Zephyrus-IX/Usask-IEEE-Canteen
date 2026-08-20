from django.contrib import admin
from django.urls import include, path

from canteen import views

urlpatterns = [
    path("", views.home, name="home"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("sales/new/", views.NewSaleView.as_view(), name="new-sale"),
    path("tabs/load-balance/", views.LoadBalanceView.as_view(), name="load-balance"),
    path("restocks/new/", views.RestockCreateView.as_view(), name="restock-create"),
    path("reports/", views.ReportsView.as_view(), name="reports"),
    path("reports/sales.csv", views.ExportSalesCsvView.as_view(), name="export-sales-csv"),
    path("reports/balance-loads.csv", views.ExportBalanceLoadsCsvView.as_view(), name="export-balance-loads-csv"),
    path("reports/restocks.csv", views.ExportRestocksCsvView.as_view(), name="export-restocks-csv"),
    path("reports/inventory.csv", views.ExportInventoryCsvView.as_view(), name="export-inventory-csv"),
    path("reports/student-tabs.csv", views.ExportStudentTabsCsvView.as_view(), name="export-student-tabs-csv"),
    path("tabs/", views.StudentTabListView.as_view(), name="student-tab-list"),
    path("tabs/new/", views.StudentTabCreateView.as_view(), name="student-tab-create"),
    path("inventory/", views.InventoryItemListView.as_view(), name="inventory-item-list"),
    path("inventory/new/", views.InventoryItemCreateView.as_view(), name="inventory-item-create"),
    path("admin/", admin.site.urls),
]
