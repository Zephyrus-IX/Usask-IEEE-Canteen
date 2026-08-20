from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import InventoryItem, StudentTab


class ManagementViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="exec", password="password")
        self.client.force_login(self.user)

    def test_home_links_to_student_tabs_and_inventory(self):
        response = self.client.get(reverse("home"))

        self.assertContains(response, reverse("student-tab-list"))
        self.assertContains(response, reverse("inventory-item-list"))

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
