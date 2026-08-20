from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import timezone


MONEY_QUANT = Decimal("0.01")


def quantize_money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


class StudentTab(models.Model):
    student_id = models.CharField(max_length=32, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_ieee_member = models.BooleanField(default=False)
    ieee_member_id = models.CharField(max_length=64, blank=True)
    ieee_membership_expires_on = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_student_tabs",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["student_id"]

    def __str__(self) -> str:
        return f"{self.student_id} - {self.first_name} {self.last_name}"

    @property
    def has_active_ieee_discount(self) -> bool:
        if not self.is_ieee_member or not self.ieee_membership_expires_on:
            return False
        return self.ieee_membership_expires_on >= timezone.localdate()

    @property
    def current_balance(self) -> Decimal:
        total = self.balance_transactions.aggregate(total=Sum("amount"))["total"]
        return total or Decimal("0.00")


class InventoryItem(models.Model):
    name = models.CharField(max_length=120, unique=True)
    quantity_on_hand = models.PositiveIntegerField(default=0)
    member_price = models.DecimalField(max_digits=8, decimal_places=2)
    non_member_price = models.DecimalField(max_digits=8, decimal_places=2)
    low_stock_threshold = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def price_for_tab(self, tab: StudentTab) -> Decimal:
        return self.member_price if tab.has_active_ieee_discount else self.non_member_price


class TaxRate(models.Model):
    name = models.CharField(max_length=32, unique=True)
    rate_percent = models.DecimalField(max_digits=6, decimal_places=3)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.rate_percent}%)"


class Sale(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = "cash", "Cash"
        CARD = "card", "Card"
        BALANCE = "balance", "Student Balance"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PAID = "paid", "Paid"
        VOID = "void", "Void"

    student_tab = models.ForeignKey(StudentTab, on_delete=models.PROTECT, related_name="sales")
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="handled_sales",
        blank=True,
        null=True,
    )
    payment_method = models.CharField(max_length=16, choices=PaymentMethod.choices)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Sale #{self.pk or 'new'} - {self.student_tab}"

    def recalculate_total(self, *, save: bool = True) -> Decimal:
        total = self.items.aggregate(total=Sum("line_total"))["total"] or Decimal("0.00")
        self.total_amount = quantize_money(total)
        if save:
            self.save(update_fields=["total_amount"])
        return self.total_amount


class SaleItemManager(models.Manager):
    def create_for_sale(self, *, sale: Sale, inventory_item: InventoryItem, quantity: int):
        unit_price = inventory_item.price_for_tab(sale.student_tab)
        return self.create(
            sale=sale,
            inventory_item=inventory_item,
            quantity=quantity,
            unit_price=unit_price,
        )


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT, related_name="sale_items")
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    line_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    objects = SaleItemManager()

    class Meta:
        ordering = ["id"]

    def save(self, *args, **kwargs):
        self.line_total = quantize_money(self.unit_price * self.quantity)
        super().save(*args, **kwargs)
        self.sale.recalculate_total()

    def __str__(self) -> str:
        return f"{self.inventory_item} x{self.quantity}"


class BalanceTransaction(models.Model):
    class TransactionType(models.TextChoices):
        LOAD = "load", "Load"
        PURCHASE = "purchase", "Purchase"
        REFUND = "refund", "Refund"
        ADJUSTMENT = "adjustment", "Adjustment"

    class PaymentMethod(models.TextChoices):
        CASH = "cash", "Cash"
        CARD = "card", "Card"
        BALANCE = "balance", "Student Balance"
        INTERNAL = "internal", "Internal"

    student_tab = models.ForeignKey(
        StudentTab,
        on_delete=models.PROTECT,
        related_name="balance_transactions",
    )
    transaction_type = models.CharField(max_length=16, choices=TransactionType.choices)
    payment_method = models.CharField(max_length=16, choices=PaymentMethod.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    related_sale = models.ForeignKey(
        Sale,
        on_delete=models.PROTECT,
        related_name="balance_transactions",
        blank=True,
        null=True,
    )
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="handled_balance_transactions",
        blank=True,
        null=True,
    )
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.student_tab}: {self.amount}"


class RestockEvent(models.Model):
    vendor = models.CharField(max_length=120, blank=True)
    restocked_on = models.DateField(default=timezone.localdate)
    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="entered_restocks",
        blank=True,
        null=True,
    )
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total_tax = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-restocked_on", "-created_at"]

    def __str__(self) -> str:
        return f"Restock {self.restocked_on} - {self.vendor or 'Unknown vendor'}"

    def recalculate_totals(self, *, save: bool = True):
        subtotal = self.items.aggregate(total=Sum("line_subtotal"))["total"] or self.subtotal
        tax = self.tax_lines.filter(was_applied=True).aggregate(total=Sum("actual_amount"))["total"] or Decimal("0.00")
        self.subtotal = quantize_money(subtotal)
        self.total_tax = quantize_money(tax)
        self.total_paid = quantize_money(self.subtotal + self.total_tax)
        if save:
            self.save(update_fields=["subtotal", "total_tax", "total_paid"])
        return self.total_paid


class RestockTaxLine(models.Model):
    restock_event = models.ForeignKey(RestockEvent, on_delete=models.CASCADE, related_name="tax_lines")
    tax_name = models.CharField(max_length=32)
    rate_percent = models.DecimalField(max_digits=6, decimal_places=3)
    calculated_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    actual_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    was_applied = models.BooleanField(default=True)

    class Meta:
        ordering = ["tax_name"]

    def save(self, *args, **kwargs):
        if not self.actual_amount:
            self.actual_amount = self.calculated_amount
        super().save(*args, **kwargs)
        self.restock_event.recalculate_totals()

    def __str__(self) -> str:
        return f"{self.tax_name}: {self.actual_amount}"


class RestockItem(models.Model):
    restock_event = models.ForeignKey(RestockEvent, on_delete=models.CASCADE, related_name="items")
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT, related_name="restock_items")
    quantity = models.PositiveIntegerField()
    line_subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["id"]

    @property
    def allocated_tax(self) -> Decimal:
        subtotal = self.restock_event.subtotal or Decimal("0.00")
        if subtotal == 0:
            return Decimal("0.00")
        ratio = self.line_subtotal / subtotal
        return quantize_money(self.restock_event.total_tax * ratio)

    @property
    def line_total(self) -> Decimal:
        return quantize_money(self.line_subtotal + self.allocated_tax)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.restock_event.recalculate_totals()

    def __str__(self) -> str:
        return f"{self.inventory_item} x{self.quantity}"


class InventoryAdjustment(models.Model):
    class AdjustmentType(models.TextChoices):
        DAMAGED = "damaged", "Damaged item"
        MISSING = "missing", "Missing item"
        COUNT_CORRECTION = "count_correction", "Count correction"
        ADMIN_CORRECTION = "admin_correction", "Admin correction"
        OTHER = "other", "Other"

    inventory_item = models.ForeignKey(
        InventoryItem,
        on_delete=models.PROTECT,
        related_name="inventory_adjustments",
    )
    adjustment_type = models.CharField(max_length=32, choices=AdjustmentType.choices)
    quantity_delta = models.IntegerField()
    reason = models.TextField()
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="inventory_adjustments",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.inventory_item}: {self.quantity_delta:+d}"
