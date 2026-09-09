from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import (
    Account,
    BalanceTransaction,
    InventoryItem,
    RestockEvent,
    RestockTaxLine,
    Sale,
    TaxRate,
)


class ManagementViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="exec", password="password", is_staff=True)
        self.client.force_login(self.user)

    def test_public_home_shows_customer_options_only(self):
        self.client.logout()

        response = self.client.get(reverse("home"))

        self.assertContains(response, reverse("new-sale"))
        self.assertContains(response, reverse("account-detail"))
        self.assertContains(response, reverse("inventory-item-list"))
        self.assertContains(response, reverse("login"))
        self.assertNotContains(response, reverse("load-balance"))
        self.assertNotContains(response, reverse("restock-create"))
        self.assertNotContains(response, reverse("reports"))
        self.assertNotContains(response, "Manage student accounts")

    def test_staff_home_links_to_management_tools(self):
        response = self.client.get(reverse("home"))

        self.assertContains(response, reverse("new-sale"))
        self.assertContains(response, reverse("load-balance"))
        self.assertContains(response, reverse("restock-create"))
        self.assertContains(response, reverse("reports"))
        self.assertContains(response, reverse("account-list"))
        self.assertContains(response, reverse("inventory-item-list"))

    def test_customer_home_shows_customer_options_only(self):
        customer = User.objects.create_user(username="abc123", password="12345678")
        Account.objects.create(user=customer, student_id="12345678", first_name="Alex", last_name="Student")
        self.client.force_login(customer)

        response = self.client.get(reverse("home"))

        self.assertContains(response, reverse("new-sale"))
        self.assertContains(response, reverse("account-detail"))
        self.assertContains(response, reverse("inventory-item-list"))
        self.assertNotContains(response, reverse("load-balance"))
        self.assertNotContains(response, reverse("restock-create"))
        self.assertNotContains(response, reverse("reports"))
        self.assertNotContains(response, "Manage student accounts")

    def test_anonymous_user_can_reach_login_page_with_account_notice(self):
        self.client.logout()

        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "NSID")
        self.assertContains(response, "Student Number")
        self.assertContains(response, "vice-chair")

    def test_login_without_next_redirects_to_canteen_home(self):
        self.client.logout()
        User.objects.create_user(username="admin", password="password", is_staff=True)

        response = self.client.post(reverse("login"), {"username": "admin", "password": "password"})

        self.assertRedirects(response, reverse("home"))

    def test_canteen_logout_redirects_to_canteen_home(self):
        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("home"))

    def test_protected_pages_redirect_to_login(self):
        self.client.logout()

        response = self.client.get(reverse("account-detail"))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('account-detail')}")

    def test_staff_only_pages_reject_customer_users(self):
        customer = User.objects.create_user(username="abc123", password="12345678")
        Account.objects.create(user=customer, student_id="12345678", first_name="Alex", last_name="Student")
        self.client.force_login(customer)

        response = self.client.get(reverse("account-list"))

        self.assertEqual(response.status_code, 403)

    def test_account_list_shows_accounts_and_create_link(self):
        Account.objects.create(student_id="12345678", first_name="Alex", last_name="Student")

        response = self.client.get(reverse("account-list"))

        self.assertContains(response, "12345678")
        self.assertContains(response, "Alex Student")
        self.assertContains(response, reverse("account-create"))

    def test_create_account_creates_login_user_with_nsid_and_student_number(self):
        response = self.client.post(
            reverse("account-create"),
            {
                "nsid": "abc123",
                "student_id": "12345678",
                "first_name": "Alex",
                "last_name": "Student",
                "is_active": "on",
                "is_ieee_member": "on",
                "ieee_member_id": "IEEE-001",
                "ieee_membership_expires_on": "2099-12-31",
                "notes": "",
            },
        )

        self.assertRedirects(response, reverse("account-list"))
        account = Account.objects.get(student_id="12345678")
        self.assertEqual(account.first_name, "Alex")
        self.assertEqual(account.created_by, self.user)
        self.assertEqual(account.user.username, "abc123")
        self.assertTrue(account.user.check_password("12345678"))

    def test_customer_account_detail_shows_own_balance_and_history(self):
        customer = User.objects.create_user(username="abc123", password="12345678")
        account = Account.objects.create(user=customer, student_id="12345678", first_name="Alex", last_name="Student")
        BalanceTransaction.objects.create(
            account=account,
            transaction_type=BalanceTransaction.TransactionType.LOAD,
            payment_method=BalanceTransaction.PaymentMethod.CASH,
            amount=Decimal("20.00"),
        )
        self.client.force_login(customer)

        response = self.client.get(reverse("account-detail"))

        self.assertContains(response, "Alex Student")
        self.assertContains(response, "$20.00")
        self.assertContains(response, "Balance history")

    def test_inventory_list_shows_items_to_customers_without_create_link(self):
        customer = User.objects.create_user(username="abc123", password="12345678")
        Account.objects.create(user=customer, student_id="12345678", first_name="Alex", last_name="Student")
        InventoryItem.objects.create(
            name="Coke",
            quantity_on_hand=24,
            member_price=Decimal("1.25"),
            non_member_price=Decimal("1.50"),
        )
        self.client.force_login(customer)

        response = self.client.get(reverse("inventory-item-list"))

        self.assertContains(response, "Coke")
        self.assertNotContains(response, reverse("inventory-item-create"))

    def test_inventory_list_shows_create_link_to_staff(self):
        InventoryItem.objects.create(
            name="Coke",
            quantity_on_hand=24,
            member_price=Decimal("1.25"),
            non_member_price=Decimal("1.50"),
        )

        response = self.client.get(reverse("inventory-item-list"))

        self.assertContains(response, "Coke")
        self.assertContains(response, "$1.25")
        self.assertContains(response, reverse("inventory-item-create"))

    def test_create_inventory_item(self):
        response = self.client.post(
            reverse("inventory-item-create"),
            {
                "name": "Coke",
                "quantity_on_hand": "24",
                "member_price": "1.25",
                "non_member_price": "1.50",
                "low_stock_threshold": "6",
                "is_active": "on",
                "notes": "",
            },
        )

        self.assertRedirects(response, reverse("inventory-item-list"))
        item = InventoryItem.objects.get(name="Coke")
        self.assertEqual(item.quantity_on_hand, 24)
        self.assertEqual(item.member_price, Decimal("1.25"))

    def test_new_sale_page_requires_login(self):
        self.client.logout()

        response = self.client.get(reverse("new-sale"))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('new-sale')}")

    def test_staff_new_sale_page_shows_account_selection_and_balance_payment(self):
        Account.objects.create(student_id="12345678", first_name="Alex", last_name="Student")
        InventoryItem.objects.create(
            name="Coke",
            quantity_on_hand=10,
            member_price=Decimal("1.25"),
            non_member_price=Decimal("1.50"),
        )

        response = self.client.get(reverse("new-sale"))

        self.assertContains(response, "New Sale")
        self.assertContains(response, "12345678 - Alex Student")
        self.assertContains(response, "Student Balance")
        self.assertContains(response, "Coke")

    def test_customer_new_sale_page_uses_own_account_and_shows_balance(self):
        customer = User.objects.create_user(username="abc123", password="12345678")
        account = Account.objects.create(user=customer, student_id="12345678", first_name="Alex", last_name="Student")
        BalanceTransaction.objects.create(
            account=account,
            transaction_type=BalanceTransaction.TransactionType.LOAD,
            payment_method=BalanceTransaction.PaymentMethod.CASH,
            amount=Decimal("10.00"),
        )
        InventoryItem.objects.create(
            name="Coke",
            quantity_on_hand=10,
            member_price=Decimal("1.25"),
            non_member_price=Decimal("1.50"),
        )
        self.client.force_login(customer)

        response = self.client.get(reverse("new-sale"))

        self.assertContains(response, "Alex Student")
        self.assertContains(response, "Current balance")
        self.assertContains(response, "$10.00")
        self.assertNotContains(response, "Account:")
        self.assertNotContains(response, "Payment method")

    def test_customer_balance_sale_from_web_form_uses_own_account(self):
        customer = User.objects.create_user(username="abc123", password="12345678")
        account = Account.objects.create(
            user=customer,
            student_id="12345678",
            first_name="Alex",
            last_name="Student",
            is_ieee_member=True,
            ieee_membership_expires_on="2099-12-31",
        )
        BalanceTransaction.objects.create(
            account=account,
            transaction_type=BalanceTransaction.TransactionType.LOAD,
            payment_method=BalanceTransaction.PaymentMethod.CASH,
            amount=Decimal("10.00"),
        )
        item = InventoryItem.objects.create(
            name="Coke",
            quantity_on_hand=10,
            member_price=Decimal("1.25"),
            non_member_price=Decimal("1.50"),
        )
        self.client.force_login(customer)

        response = self.client.post(
            reverse("new-sale"),
            {
                "item_1": str(item.pk),
                "quantity_1": "2",
            },
        )

        self.assertRedirects(response, reverse("new-sale"))
        item.refresh_from_db()
        sale = Sale.objects.get()
        self.assertEqual(sale.account, account)
        self.assertEqual(sale.payment_method, Sale.PaymentMethod.BALANCE)
        self.assertEqual(sale.total_amount, Decimal("2.50"))
        self.assertEqual(account.current_balance, Decimal("7.50"))
        self.assertEqual(item.quantity_on_hand, 8)

    def test_staff_balance_sale_from_web_form_can_select_account(self):
        account = Account.objects.create(student_id="12345678", first_name="Alex", last_name="Student")
        BalanceTransaction.objects.create(
            account=account,
            transaction_type=BalanceTransaction.TransactionType.LOAD,
            payment_method=BalanceTransaction.PaymentMethod.CASH,
            amount=Decimal("10.00"),
        )
        item = InventoryItem.objects.create(
            name="Coke",
            quantity_on_hand=10,
            member_price=Decimal("1.25"),
            non_member_price=Decimal("1.50"),
        )

        response = self.client.post(
            reverse("new-sale"),
            {
                "account": str(account.pk),
                "item_1": str(item.pk),
                "quantity_1": "2",
            },
        )

        self.assertRedirects(response, reverse("new-sale"))
        sale = Sale.objects.get()
        self.assertEqual(sale.account, account)
        self.assertEqual(sale.payment_method, Sale.PaymentMethod.BALANCE)
        self.assertEqual(sale.total_amount, Decimal("3.00"))

    def test_load_balance_page_requires_staff(self):
        customer = User.objects.create_user(username="abc123", password="12345678")
        Account.objects.create(user=customer, student_id="12345678", first_name="Alex", last_name="Student")
        self.client.force_login(customer)

        response = self.client.get(reverse("load-balance"))

        self.assertEqual(response.status_code, 403)

    def test_load_balance_page_shows_active_accounts(self):
        Account.objects.create(student_id="12345678", first_name="Alex", last_name="Student")

        response = self.client.get(reverse("load-balance"))

        self.assertContains(response, "Load Account Balance")
        self.assertContains(response, "12345678 - Alex Student")

    def test_load_balance_from_web_form(self):
        account = Account.objects.create(student_id="12345678", first_name="Alex", last_name="Student")

        response = self.client.post(
            reverse("load-balance"),
            {
                "account": str(account.pk),
                "amount": "20.00",
                "payment_method": BalanceTransaction.PaymentMethod.CASH,
                "note": "Initial load",
            },
        )

        self.assertRedirects(response, reverse("load-balance"))
        transaction = BalanceTransaction.objects.get()
        self.assertEqual(transaction.amount, Decimal("20.00"))
        self.assertEqual(transaction.transaction_type, BalanceTransaction.TransactionType.LOAD)
        self.assertEqual(transaction.handled_by, self.user)
        self.assertEqual(account.current_balance, Decimal("20.00"))

    def test_restock_page_requires_staff(self):
        customer = User.objects.create_user(username="abc123", password="12345678")
        Account.objects.create(user=customer, student_id="12345678", first_name="Alex", last_name="Student")
        self.client.force_login(customer)

        response = self.client.get(reverse("restock-create"))

        self.assertEqual(response.status_code, 403)

    def test_restock_page_shows_items_and_active_taxes(self):
        InventoryItem.objects.create(
            name="Coke",
            quantity_on_hand=10,
            member_price=Decimal("1.25"),
            non_member_price=Decimal("1.50"),
        )
        TaxRate.objects.create(name="GST", rate_percent=Decimal("5.000"))

        response = self.client.get(reverse("restock-create"))

        self.assertContains(response, "New Restock")
        self.assertContains(response, "Coke")
        self.assertContains(response, "GST")

    def test_create_restock_from_web_form(self):
        coke = InventoryItem.objects.create(
            name="Coke",
            quantity_on_hand=10,
            member_price=Decimal("1.25"),
            non_member_price=Decimal("1.50"),
        )
        chips = InventoryItem.objects.create(
            name="Chips",
            quantity_on_hand=5,
            member_price=Decimal("1.50"),
            non_member_price=Decimal("2.00"),
        )
        gst = TaxRate.objects.create(name="GST", rate_percent=Decimal("5.000"))
        pst = TaxRate.objects.create(name="PST", rate_percent=Decimal("6.000"))

        response = self.client.post(
            reverse("restock-create"),
            {
                "vendor": "Costco",
                "item_1": str(coke.pk),
                "quantity_1": "24",
                "line_subtotal_1": "18.00",
                "item_2": str(chips.pk),
                "quantity_2": "10",
                "line_subtotal_2": "20.00",
                "tax_rates": [str(gst.pk), str(pst.pk)],
                "notes": "Test receipt",
            },
        )

        self.assertRedirects(response, reverse("restock-create"))
        coke.refresh_from_db()
        chips.refresh_from_db()
        restock = RestockEvent.objects.get()
        self.assertEqual(coke.quantity_on_hand, 34)
        self.assertEqual(chips.quantity_on_hand, 15)
        self.assertEqual(restock.subtotal, Decimal("38.00"))
        self.assertEqual(restock.total_tax, Decimal("4.18"))
        self.assertEqual(restock.total_paid, Decimal("42.18"))
        self.assertEqual(RestockTaxLine.objects.filter(restock_event=restock).count(), 2)

    def test_reports_page_requires_staff(self):
        customer = User.objects.create_user(username="abc123", password="12345678")
        Account.objects.create(user=customer, student_id="12345678", first_name="Alex", last_name="Student")
        self.client.force_login(customer)

        response = self.client.get(reverse("reports"))

        self.assertEqual(response.status_code, 403)

    def test_reports_page_links_to_csv_exports(self):
        response = self.client.get(reverse("reports"))

        self.assertContains(response, "Reports")
        self.assertContains(response, reverse("export-sales-csv"))
        self.assertContains(response, reverse("export-balance-loads-csv"))
        self.assertContains(response, reverse("export-restocks-csv"))
        self.assertContains(response, reverse("export-inventory-csv"))
        self.assertContains(response, reverse("export-accounts-csv"))

    def test_sales_csv_export(self):
        account = Account.objects.create(student_id="12345678", first_name="Alex", last_name="Student")
        item = InventoryItem.objects.create(
            name="Coke",
            quantity_on_hand=10,
            member_price=Decimal("1.25"),
            non_member_price=Decimal("1.50"),
        )
        BalanceTransaction.objects.create(
            account=account,
            transaction_type=BalanceTransaction.TransactionType.LOAD,
            payment_method=BalanceTransaction.PaymentMethod.CASH,
            amount=Decimal("10.00"),
        )
        self.client.post(
            reverse("new-sale"),
            {
                "account": str(account.pk),
                "item_1": str(item.pk),
                "quantity_1": "2",
            },
        )

        response = self.client.get(reverse("export-sales-csv"))

        self.assertEqual(response["Content-Type"], "text/csv")
        content = response.content.decode()
        self.assertIn("sale_id,created_at,student_id,student_name,payment_method,status,total_amount", content)
        self.assertIn("12345678", content)
        self.assertIn("3.00", content)

    def test_balance_loads_csv_export(self):
        account = Account.objects.create(student_id="12345678", first_name="Alex", last_name="Student")
        BalanceTransaction.objects.create(
            account=account,
            transaction_type=BalanceTransaction.TransactionType.LOAD,
            payment_method=BalanceTransaction.PaymentMethod.CASH,
            amount=Decimal("20.00"),
        )

        response = self.client.get(reverse("export-balance-loads-csv"))

        self.assertEqual(response["Content-Type"], "text/csv")
        content = response.content.decode()
        self.assertIn("transaction_id,created_at,student_id,student_name,payment_method,amount,note", content)
        self.assertIn("20.00", content)

    def test_inventory_csv_export(self):
        InventoryItem.objects.create(
            name="Coke",
            quantity_on_hand=10,
            member_price=Decimal("1.25"),
            non_member_price=Decimal("1.50"),
        )

        response = self.client.get(reverse("export-inventory-csv"))

        self.assertEqual(response["Content-Type"], "text/csv")
        content = response.content.decode()
        self.assertIn("name,quantity_on_hand,member_price,non_member_price,low_stock_threshold,is_active", content)
        self.assertIn("Coke", content)

    def test_accounts_csv_export(self):
        Account.objects.create(student_id="12345678", first_name="Alex", last_name="Student")

        response = self.client.get(reverse("export-accounts-csv"))

        self.assertEqual(response["Content-Type"], "text/csv")
        content = response.content.decode()
        self.assertIn("student_id,nsid,first_name,last_name,is_active,is_ieee_member", content)
        self.assertIn("12345678", content)

    def test_restocks_csv_export(self):
        RestockEvent.objects.create(vendor="Costco", subtotal=Decimal("10.00"), total_tax=Decimal("1.10"), total_paid=Decimal("11.10"))

        response = self.client.get(reverse("export-restocks-csv"))

        self.assertEqual(response["Content-Type"], "text/csv")
        content = response.content.decode()
        self.assertIn("restock_id,restocked_on,vendor,subtotal,total_tax,total_paid", content)
        self.assertIn("Costco", content)
