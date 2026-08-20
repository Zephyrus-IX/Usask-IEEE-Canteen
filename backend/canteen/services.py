from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F

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
    quantize_money,
)


def _positive_decimal(value: Decimal, message: str) -> Decimal:
    value = quantize_money(value)
    if value <= 0:
        raise ValidationError(message)
    return value


def load_student_balance(
    *,
    student_tab: StudentTab,
    amount: Decimal,
    payment_method: str,
    handled_by=None,
    note: str = "",
) -> BalanceTransaction:
    if not student_tab.is_active:
        raise ValidationError("Student tab is inactive")
    amount = _positive_decimal(amount, "Balance load amount must be positive")
    if payment_method not in {BalanceTransaction.PaymentMethod.CASH, BalanceTransaction.PaymentMethod.CARD}:
        raise ValidationError("Balance loads must be paid by cash or card")

    return BalanceTransaction.objects.create(
        student_tab=student_tab,
        transaction_type=BalanceTransaction.TransactionType.LOAD,
        payment_method=payment_method,
        amount=amount,
        handled_by=handled_by,
        note=note,
    )


@transaction.atomic
def create_sale(
    *,
    student_tab: StudentTab,
    items: list[dict],
    payment_method: str,
    handled_by=None,
) -> Sale:
    if not student_tab.is_active:
        raise ValidationError("Student tab is inactive")
    if payment_method not in Sale.PaymentMethod.values:
        raise ValidationError("Invalid payment method")
    if not items:
        raise ValidationError("Sale must contain at least one item")

    locked_items: list[tuple[InventoryItem, int]] = []
    for item_data in items:
        inventory_item = InventoryItem.objects.select_for_update().get(pk=item_data["inventory_item"].pk)
        quantity = int(item_data["quantity"])
        if quantity <= 0:
            raise ValidationError("Sale item quantity must be positive")
        if not inventory_item.is_active:
            raise ValidationError(f"Inventory item is inactive: {inventory_item.name}")
        if inventory_item.quantity_on_hand < quantity:
            raise ValidationError(f"Insufficient inventory for {inventory_item.name}")
        locked_items.append((inventory_item, quantity))

    sale = Sale.objects.create(
        student_tab=student_tab,
        handled_by=handled_by,
        payment_method=payment_method,
        status=Sale.Status.DRAFT,
    )

    for inventory_item, quantity in locked_items:
        SaleItem.objects.create_for_sale(
            sale=sale,
            inventory_item=inventory_item,
            quantity=quantity,
        )

    sale.recalculate_total()

    if payment_method == Sale.PaymentMethod.BALANCE:
        current_balance = StudentTab.objects.get(pk=student_tab.pk).current_balance
        if current_balance < sale.total_amount:
            raise ValidationError("Insufficient student balance")
        BalanceTransaction.objects.create(
            student_tab=student_tab,
            transaction_type=BalanceTransaction.TransactionType.PURCHASE,
            payment_method=BalanceTransaction.PaymentMethod.BALANCE,
            amount=-sale.total_amount,
            related_sale=sale,
            handled_by=handled_by,
        )

    for inventory_item, quantity in locked_items:
        InventoryItem.objects.filter(pk=inventory_item.pk).update(
            quantity_on_hand=F("quantity_on_hand") - quantity
        )

    sale.status = Sale.Status.PAID
    sale.save(update_fields=["status"])
    return sale


@transaction.atomic
def record_restock(
    *,
    vendor: str = "",
    items: list[dict],
    tax_rates: list[TaxRate] | None = None,
    tax_overrides: dict[str, Decimal] | None = None,
    entered_by=None,
    notes: str = "",
) -> RestockEvent:
    if not items:
        raise ValidationError("Restock must contain at least one item")
    tax_rates = tax_rates or []
    tax_overrides = tax_overrides or {}

    subtotal = Decimal("0.00")
    normalized_items: list[tuple[InventoryItem, int, Decimal]] = []
    for item_data in items:
        inventory_item = InventoryItem.objects.select_for_update().get(pk=item_data["inventory_item"].pk)
        quantity = int(item_data["quantity"])
        if quantity <= 0:
            raise ValidationError("Restock item quantity must be positive")
        line_subtotal = _positive_decimal(item_data["line_subtotal"], "Restock line subtotal must be positive")
        subtotal += line_subtotal
        normalized_items.append((inventory_item, quantity, line_subtotal))

    event = RestockEvent.objects.create(
        vendor=vendor,
        entered_by=entered_by,
        subtotal=quantize_money(subtotal),
        notes=notes,
    )

    for inventory_item, quantity, line_subtotal in normalized_items:
        RestockItem.objects.create(
            restock_event=event,
            inventory_item=inventory_item,
            quantity=quantity,
            line_subtotal=line_subtotal,
        )

    for tax_rate in tax_rates:
        calculated_amount = quantize_money(event.subtotal * tax_rate.rate_percent / Decimal("100"))
        actual_amount = quantize_money(tax_overrides.get(tax_rate.name, calculated_amount))
        RestockTaxLine.objects.create(
            restock_event=event,
            tax_name=tax_rate.name,
            rate_percent=tax_rate.rate_percent,
            calculated_amount=calculated_amount,
            actual_amount=actual_amount,
            was_applied=True,
        )

    event.recalculate_totals()

    for inventory_item, quantity, _line_subtotal in normalized_items:
        InventoryItem.objects.filter(pk=inventory_item.pk).update(
            quantity_on_hand=F("quantity_on_hand") + quantity
        )

    return event


@transaction.atomic
def adjust_inventory(
    *,
    inventory_item: InventoryItem,
    quantity_delta: int,
    adjustment_type: str,
    reason: str,
    handled_by=None,
) -> InventoryAdjustment:
    if not reason.strip():
        raise ValidationError("Inventory adjustment reason is required")
    if quantity_delta == 0:
        raise ValidationError("Inventory adjustment quantity cannot be zero")
    if adjustment_type not in InventoryAdjustment.AdjustmentType.values:
        raise ValidationError("Invalid inventory adjustment type")

    item = InventoryItem.objects.select_for_update().get(pk=inventory_item.pk)
    if item.quantity_on_hand + quantity_delta < 0:
        raise ValidationError("Inventory adjustment cannot make quantity negative")

    adjustment = InventoryAdjustment.objects.create(
        inventory_item=item,
        adjustment_type=adjustment_type,
        quantity_delta=quantity_delta,
        reason=reason,
        handled_by=handled_by,
    )
    InventoryItem.objects.filter(pk=item.pk).update(quantity_on_hand=F("quantity_on_hand") + quantity_delta)
    return adjustment
