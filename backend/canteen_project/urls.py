from django.contrib import admin
from django.urls import include, path

from canteen import views

urlpatterns = [
    path("", views.home, name="home"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("sales/new/", views.NewSaleView.as_view(), name="new-sale"),
    path("tabs/", views.StudentTabListView.as_view(), name="student-tab-list"),
    path("tabs/new/", views.StudentTabCreateView.as_view(), name="student-tab-create"),
    path("inventory/", views.InventoryItemListView.as_view(), name="inventory-item-list"),
    path("inventory/new/", views.InventoryItemCreateView.as_view(), name="inventory-item-create"),
    path("admin/", admin.site.urls),
]
