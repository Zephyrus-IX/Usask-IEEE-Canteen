from django.contrib import admin

from .models import (
    BalanceTransaction,
    InventoryAdjustment,
    InventoryItem,
    RestockEvent,
    RestockItem,
    RestockTaxLine,
    Sale,
    SaleItem,
    StudentTab,
    TaxRate,
)


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
        "current_balance",
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


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ("line_total",)


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("id", "student_tab", "payment_method", "status", "total_amount", "created_at")
    list_filter = ("payment_method", "status", "created_at")
    search_fields = ("student_tab__student_id", "student_tab__first_name", "student_tab__last_name")
    inlines = [SaleItemInline]


@admin.register(BalanceTransaction)
class BalanceTransactionAdmin(admin.ModelAdmin):
    list_display = ("student_tab", "transaction_type", "payment_method", "amount", "created_at")
    list_filter = ("transaction_type", "payment_method", "created_at")
    search_fields = ("student_tab__student_id", "student_tab__first_name", "student_tab__last_name")


class RestockItemInline(admin.TabularInline):
    model = RestockItem
    extra = 0
    readonly_fields = ("allocated_tax", "line_total")


class RestockTaxLineInline(admin.TabularInline):
    model = RestockTaxLine
    extra = 0


@admin.register(RestockEvent)
class RestockEventAdmin(admin.ModelAdmin):
    list_display = ("id", "vendor", "restocked_on", "subtotal", "total_tax", "total_paid")
    list_filter = ("restocked_on",)
    search_fields = ("vendor",)
    inlines = [RestockItemInline, RestockTaxLineInline]


@admin.register(InventoryAdjustment)
class InventoryAdjustmentAdmin(admin.ModelAdmin):
    list_display = ("inventory_item", "adjustment_type", "quantity_delta", "created_at")
    list_filter = ("adjustment_type", "created_at")
    search_fields = ("inventory_item__name", "reason")
