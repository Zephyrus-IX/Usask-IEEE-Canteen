from django.contrib import admin

from .models import InventoryItem, StudentTab, TaxRate


@admin.register(StudentTab)
class StudentTabAdmin(admin.ModelAdmin):
    list_display = (
        "student_id",
        "first_name",
        "last_name",
        "is_active",
        "is_ieee_member",
        "ieee_membership_expires_on",
        "has_active_ieee_discount",
    )
    search_fields = ("student_id", "first_name", "last_name", "ieee_member_id")
    list_filter = ("is_active", "is_ieee_member")


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "quantity_on_hand",
        "member_price",
        "non_member_price",
        "low_stock_threshold",
        "is_active",
    )
    search_fields = ("name",)
    list_filter = ("is_active",)


@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    list_display = ("name", "rate_percent", "is_active")
    list_filter = ("is_active",)
