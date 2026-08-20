from datetime import date
from decimal import Decimal

from django.test import TestCase

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
)


class CanteenModelTests(TestCase):
    def test_sale_item_uses_member_price_and_calculates_line_total(self):
        tab = StudentTab.objects.create(
            student_id="12345678",
            first_name="Alex",
            last_name="Student",
            is_ieee_member=True,
            ieee_membership_expires_on=date(2099, 12, 31),
        )
        item = InventoryItem.objects.create(
            name="Coke",
            quantity_on_hand=24,
            member_price=Decimal("1.25"),
            non_member_price=Decimal("1.50"),
        )
        sale = Sale.objects.create(student_tab=tab, payment_method=Sale.PaymentMethod.CASH)

        sale_item = SaleItem.objects.create_for_sale(sale=sale, inventory_item=item, quantity=2)

        self.assertEqual(sale_item.unit_price, Decimal("1.25"))
        self.assertEqual(sale_item.line_total, Decimal("2.50"))

    def test_student_balance_is_sum_of_balance_transactions(self):
        tab = StudentTab.objects.create(student_id="12345678", first_name="Alex", last_name="Student")

        BalanceTransaction.objects.create(
            student_tab=tab,
            transaction_type=BalanceTransaction.TransactionType.LOAD,
            payment_method=BalanceTransaction.PaymentMethod.CASH,
            amount=Decimal("20.00"),
        )
        BalanceTransaction.objects.create(
            student_tab=tab,
            transaction_type=BalanceTransaction.TransactionType.PURCHASE,
            payment_method=BalanceTransaction.PaymentMethod.BALANCE,
            amount=Decimal("-3.50"),
        )

        self.assertEqual(tab.current_balance, Decimal("16.50"))

    def test_restock_item_allocates_tax_proportionally(self):
        coke = InventoryItem.objects.create(
            name="Coke",
            quantity_on_hand=0,
            member_price=Decimal("1.25"),
            non_member_price=Decimal("1.50"),
        )
        chips = InventoryItem.objects.create(
            name="Chips",
            quantity_on_hand=0,
            member_price=Decimal("1.50"),
            non_member_price=Decimal("2.00"),
        )
        event = RestockEvent.objects.create(vendor="Costco", subtotal=Decimal("30.00"))
        RestockTaxLine.objects.create(
            restock_event=event,
            tax_name="GST",
            rate_percent=Decimal("5.000"),
            calculated_amount=Decimal("1.50"),
            actual_amount=Decimal("1.50"),
            was_applied=True,
        )
        coke_line = RestockItem.objects.create(
            restock_event=event,
            inventory_item=coke,
            quantity=10,
            line_subtotal=Decimal("10.00"),
        )
        chips_line = RestockItem.objects.create(
            restock_event=event,
            inventory_item=chips,
            quantity=10,
            line_subtotal=Decimal("20.00"),
        )

        self.assertEqual(coke_line.allocated_tax, Decimal("0.50"))
        self.assertEqual(chips_line.allocated_tax, Decimal("1.00"))
        self.assertEqual(coke_line.line_total, Decimal("10.50"))
        self.assertEqual(chips_line.line_total, Decimal("21.00"))

    def test_inventory_adjustment_signed_quantity_delta(self):
        item = InventoryItem.objects.create(
            name="Coke",
            quantity_on_hand=10,
            member_price=Decimal("1.25"),
            non_member_price=Decimal("1.50"),
        )

        adjustment = InventoryAdjustment.objects.create(
            inventory_item=item,
            adjustment_type=InventoryAdjustment.AdjustmentType.MISSING,
            quantity_delta=-2,
            reason="Found two missing during count",
        )

        self.assertEqual(adjustment.quantity_delta, -2)
