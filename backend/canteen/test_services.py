from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import (
    BalanceTransaction,
    InventoryItem,
    RestockTaxLine,
    Sale,
    StudentTab,
    TaxRate,
)
from .services import adjust_inventory, create_sale, load_student_balance, record_restock


class CanteenServiceTests(TestCase):
    def setUp(self):
        self.tab = StudentTab.objects.create(
            student_id="12345678",
            first_name="Alex",
            last_name="Student",
            is_ieee_member=True,
            ieee_membership_expires_on=date(2099, 12, 31),
        )
        self.coke = InventoryItem.objects.create(
            name="Coke",
            quantity_on_hand=10,
            member_price=Decimal("1.25"),
            non_member_price=Decimal("1.50"),
        )

    def test_create_sale_requires_active_tab(self):
        self.tab.is_active = False
        self.tab.save(update_fields=["is_active"])

        with self.assertRaisesMessage(ValidationError, "Student tab is inactive"):
            create_sale(
                student_tab=self.tab,
                items=[{"inventory_item": self.coke, "quantity": 1}],
                payment_method=Sale.PaymentMethod.CASH,
            )

    def test_create_cash_sale_reduces_inventory_and_marks_paid(self):
        sale = create_sale(
            student_tab=self.tab,
            items=[{"inventory_item": self.coke, "quantity": 2}],
            payment_method=Sale.PaymentMethod.CASH,
        )

        self.coke.refresh_from_db()
        self.assertEqual(sale.status, Sale.Status.PAID)
        self.assertEqual(sale.total_amount, Decimal("2.50"))
        self.assertEqual(self.coke.quantity_on_hand, 8)

    def test_create_balance_sale_requires_sufficient_balance(self):
        with self.assertRaisesMessage(ValidationError, "Insufficient student balance"):
            create_sale(
                student_tab=self.tab,
                items=[{"inventory_item": self.coke, "quantity": 1}],
                payment_method=Sale.PaymentMethod.BALANCE,
            )

    def test_create_balance_sale_deducts_student_balance(self):
        load_student_balance(
            student_tab=self.tab,
            amount=Decimal("10.00"),
            payment_method=BalanceTransaction.PaymentMethod.CASH,
        )

        sale = create_sale(
            student_tab=self.tab,
            items=[{"inventory_item": self.coke, "quantity": 2}],
            payment_method=Sale.PaymentMethod.BALANCE,
        )

        self.assertEqual(sale.total_amount, Decimal("2.50"))
        self.assertEqual(self.tab.current_balance, Decimal("7.50"))

    def test_create_sale_blocks_insufficient_inventory(self):
        with self.assertRaisesMessage(ValidationError, "Insufficient inventory"):
            create_sale(
                student_tab=self.tab,
                items=[{"inventory_item": self.coke, "quantity": 99}],
                payment_method=Sale.PaymentMethod.CASH,
            )

    def test_load_student_balance_requires_positive_amount(self):
        with self.assertRaisesMessage(ValidationError, "Balance load amount must be positive"):
            load_student_balance(
                student_tab=self.tab,
                amount=Decimal("0.00"),
                payment_method=BalanceTransaction.PaymentMethod.CASH,
            )

    def test_record_restock_applies_selected_taxes_and_increases_inventory(self):
        gst = TaxRate.objects.create(name="GST", rate_percent=Decimal("5.000"))
        pst = TaxRate.objects.create(name="PST", rate_percent=Decimal("6.000"))

        restock = record_restock(
            vendor="Costco",
            items=[{"inventory_item": self.coke, "quantity": 24, "line_subtotal": Decimal("18.00")}],
            tax_rates=[gst, pst],
        )

        self.coke.refresh_from_db()
        self.assertEqual(self.coke.quantity_on_hand, 34)
        self.assertEqual(restock.subtotal, Decimal("18.00"))
        self.assertEqual(restock.total_tax, Decimal("1.98"))
        self.assertEqual(restock.total_paid, Decimal("19.98"))
        self.assertEqual(RestockTaxLine.objects.filter(restock_event=restock).count(), 2)

    def test_adjust_inventory_changes_quantity_and_records_reason(self):
        adjustment = adjust_inventory(
            inventory_item=self.coke,
            quantity_delta=-2,
            adjustment_type="missing",
            reason="Two cans missing during count",
        )

        self.coke.refresh_from_db()
        self.assertEqual(self.coke.quantity_on_hand, 8)
        self.assertEqual(adjustment.reason, "Two cans missing during count")
