from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import InventoryItem, Sale, StudentTab


class ManagementViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="exec", password="password")
        self.client.force_login(self.user)

    def test_home_links_to_student_tabs_and_inventory(self):
        response = self.client.get(reverse("home"))

        self.assertContains(response, reverse("new-sale"))
        self.assertContains(response, reverse("student-tab-list"))
        self.assertContains(response, reverse("inventory-item-list"))

    def test_anonymous_user_can_reach_login_page(self):
        self.client.logout()

        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Login")

    def test_protected_pages_redirect_to_login(self):
        self.client.logout()

        response = self.client.get(reverse("student-tab-list"))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('student-tab-list')}")

    def test_student_tab_list_shows_tabs_and_create_link(self):
        StudentTab.objects.create(student_id="12345678", first_name="Alex", last_name="Student")

        response = self.client.get(reverse("student-tab-list"))

        self.assertContains(response, "12345678")
        self.assertContains(response, "Alex Student")
        self.assertContains(response, reverse("student-tab-create"))

    def test_create_student_tab(self):
        response = self.client.post(
            reverse("student-tab-create"),
            {
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

        self.assertRedirects(response, reverse("student-tab-list"))
        tab = StudentTab.objects.get(student_id="12345678")
        self.assertEqual(tab.first_name, "Alex")
        self.assertEqual(tab.created_by, self.user)

    def test_inventory_list_shows_items_and_create_link(self):
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

    def test_new_sale_page_shows_active_tabs_and_inventory(self):
        StudentTab.objects.create(student_id="12345678", first_name="Alex", last_name="Student")
        InventoryItem.objects.create(
            name="Coke",
            quantity_on_hand=10,
            member_price=Decimal("1.25"),
            non_member_price=Decimal("1.50"),
        )

        response = self.client.get(reverse("new-sale"))

        self.assertContains(response, "New Sale")
        self.assertContains(response, "12345678 - Alex Student")
        self.assertContains(response, "Coke")

    def test_create_cash_sale_from_web_form(self):
        tab = StudentTab.objects.create(
            student_id="12345678",
            first_name="Alex",
            last_name="Student",
            is_ieee_member=True,
            ieee_membership_expires_on="2099-12-31",
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
                "student_tab": str(tab.pk),
                "payment_method": Sale.PaymentMethod.CASH,
                "item": str(item.pk),
                "quantity": "2",
            },
        )

        self.assertRedirects(response, reverse("new-sale"))
        item.refresh_from_db()
        sale = Sale.objects.get()
        self.assertEqual(sale.total_amount, Decimal("2.50"))
        self.assertEqual(sale.status, Sale.Status.PAID)
        self.assertEqual(item.quantity_on_hand, 8)
