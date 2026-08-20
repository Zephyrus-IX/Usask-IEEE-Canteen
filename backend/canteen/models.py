from django.conf import settings
from django.db import models
from django.utils import timezone


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

    def price_for_tab(self, tab: StudentTab):
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
