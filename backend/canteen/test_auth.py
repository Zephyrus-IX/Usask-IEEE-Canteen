from datetime import timedelta

from axes.models import AccessAttempt
from django.contrib.auth.models import User
from django.core.exceptions import FieldDoesNotExist
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

from .models import Account, InventoryItem


class CustomerCredentialTests(TestCase):
    def setUp(self):
        self.exec_user = User.objects.create_user(
            username="exec",
            password="exec-password",
            is_staff=True,
        )

    def test_account_no_longer_stores_student_number(self):
        with self.assertRaises(FieldDoesNotExist):
            Account._meta.get_field("student_id")

    def test_account_requires_a_linked_nsid_user(self):
        self.assertFalse(Account._meta.get_field("user").null)
        self.assertFalse(Account._meta.get_field("user").blank)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Account.objects.create(first_name="Unlinked", last_name="Student")

    def test_exec_creates_account_with_one_time_temporary_password(self):
        self.client.force_login(self.exec_user)

        response = self.client.post(
            reverse("account-create"),
            {
                "nsid": "abc123",
                "first_name": "Alex",
                "last_name": "Student",
                "is_active": "on",
                "notes": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        account = Account.objects.select_related("user").get()
        temporary_password = response.context["temporary_password"]
        self.assertEqual(account.user.username, "abc123")
        self.assertTrue(account.user.check_password(temporary_password))
        self.assertTrue(account.must_change_password)
        self.assertGreaterEqual(len(temporary_password), 16)
        self.assertContains(response, temporary_password)
        self.assertContains(response, "shown only once")
        self.assertEqual(response["Cache-Control"], "max-age=0, no-cache, no-store, must-revalidate, private")

    def test_temporary_password_forces_password_setup_before_other_pages(self):
        customer = User.objects.create_user(username="abc123", password="temporary-password")
        Account.objects.create(user=customer, first_name="Alex", last_name="Student", must_change_password=True)

        response = self.client.post(
            reverse("login"),
            {"username": "abc123", "password": "temporary-password"},
            follow=True,
        )

        self.assertEqual(response.resolver_match.url_name, "set-password")
        self.assertContains(response, "Do not include")

        blocked_response = self.client.get(reverse("new-sale"))
        self.assertRedirects(blocked_response, reverse("set-password"))

    def test_customer_can_replace_temporary_password(self):
        customer = User.objects.create_user(username="abc123", password="temporary-password")
        account = Account.objects.create(
            user=customer,
            first_name="Alex",
            last_name="Student",
            must_change_password=True,
        )
        self.client.force_login(customer)

        response = self.client.post(
            reverse("set-password"),
            {
                "new_password1": "Correct-Horse-Battery-Staple-29",
                "new_password2": "Correct-Horse-Battery-Staple-29",
            },
        )

        self.assertRedirects(response, reverse("home"))
        customer.refresh_from_db()
        account.refresh_from_db()
        self.assertTrue(customer.check_password("Correct-Horse-Battery-Staple-29"))
        self.assertFalse(account.must_change_password)

    def test_customer_without_temporary_password_flag_cannot_use_forced_change_endpoint(self):
        customer = User.objects.create_user(username="abc123", password="current-password")
        Account.objects.create(
            user=customer,
            first_name="Alex",
            last_name="Student",
            must_change_password=False,
        )
        self.client.force_login(customer)

        response = self.client.post(
            reverse("set-password"),
            {
                "new_password1": "Replacement-Password-That-Should-Fail-29",
                "new_password2": "Replacement-Password-That-Should-Fail-29",
            },
        )

        self.assertEqual(response.status_code, 403)
        customer.refresh_from_db()
        self.assertTrue(customer.check_password("current-password"))

    def test_staff_cannot_use_customer_forced_change_endpoint(self):
        self.client.force_login(self.exec_user)

        response = self.client.get(reverse("set-password"))

        self.assertEqual(response.status_code, 403)

    def test_password_setup_rejects_password_containing_nsid(self):
        customer = User.objects.create_user(username="abc123", password="temporary-password")
        Account.objects.create(user=customer, first_name="Alex", last_name="Student", must_change_password=True)
        self.client.force_login(customer)

        response = self.client.post(
            reverse("set-password"),
            {
                "new_password1": "abc123-is-my-canteen-password",
                "new_password2": "abc123-is-my-canteen-password",
            },
        )

        self.assertContains(response, "too similar")

    def test_exec_can_reset_customer_password_and_sees_it_once(self):
        customer = User.objects.create_user(username="abc123", password="old-password")
        account = Account.objects.create(
            user=customer,
            first_name="Alex",
            last_name="Student",
            must_change_password=False,
        )
        self.client.force_login(self.exec_user)

        response = self.client.post(reverse("account-reset-password", args=[account.pk]))

        self.assertEqual(response.status_code, 200)
        temporary_password = response.context["temporary_password"]
        customer.refresh_from_db()
        account.refresh_from_db()
        self.assertFalse(customer.check_password("old-password"))
        self.assertTrue(customer.check_password(temporary_password))
        self.assertTrue(account.must_change_password)
        self.assertContains(response, temporary_password)
        self.assertEqual(response["Cache-Control"], "max-age=0, no-cache, no-store, must-revalidate, private")

    def test_customer_cannot_reset_another_account_password(self):
        customer = User.objects.create_user(username="abc123", password="customer-password")
        customer_account = Account.objects.create(
            user=customer,
            first_name="Alex",
            last_name="Student",
            must_change_password=False,
        )
        other = User.objects.create_user(username="xyz789", password="other-password")
        other_account = Account.objects.create(
            user=other,
            first_name="Other",
            last_name="Student",
            must_change_password=False,
        )
        self.client.force_login(customer)

        response = self.client.post(reverse("account-reset-password", args=[other_account.pk]))

        self.assertEqual(response.status_code, 403)
        other.refresh_from_db()
        self.assertTrue(other.check_password("other-password"))
        self.assertEqual(customer.canteen_account, customer_account)

    def test_staff_cannot_reset_an_account_linked_to_another_staff_user(self):
        elevated_user = User.objects.create_user(
            username="another-exec",
            password="elevated-password",
            is_staff=True,
        )
        elevated_account = Account.objects.create(
            user=elevated_user,
            first_name="Another",
            last_name="Exec",
            must_change_password=False,
        )
        self.client.force_login(self.exec_user)

        response = self.client.post(reverse("account-reset-password", args=[elevated_account.pk]))

        self.assertEqual(response.status_code, 403)
        elevated_user.refresh_from_db()
        self.assertTrue(elevated_user.check_password("elevated-password"))

    def test_anonymous_self_service_password_reset_routes_are_not_registered(self):
        with self.assertRaises(NoReverseMatch):
            reverse("password_reset")
        self.assertEqual(self.client.get("/accounts/password_reset/").status_code, 404)

    def test_exec_password_reset_clears_login_lockout(self):
        customer = User.objects.create_user(username="locked123", password="old-password")
        account = Account.objects.create(
            user=customer,
            first_name="Locked",
            last_name="Student",
            must_change_password=False,
        )
        for _ in range(5):
            self.client.post(reverse("login"), {"username": "locked123", "password": "wrong-password"})
        self.client.force_login(self.exec_user)

        reset_response = self.client.post(reverse("account-reset-password", args=[account.pk]))
        temporary_password = reset_response.context["temporary_password"]
        self.client.logout()
        login_response = self.client.post(
            reverse("login"),
            {"username": "locked123", "password": temporary_password},
            follow=True,
        )

        self.assertEqual(login_response.resolver_match.url_name, "set-password")

    def test_login_locks_nsid_after_five_failed_attempts(self):
        User.objects.create_user(username="locked123", password="correct-password")

        responses = [
            self.client.post(reverse("login"), {"username": "locked123", "password": "wrong-password"})
            for _ in range(5)
        ]
        blocked_response = self.client.post(
            reverse("login"),
            {"username": "locked123", "password": "correct-password"},
        )

        self.assertEqual(responses[-1].status_code, 429)
        self.assertEqual(blocked_response.status_code, 429)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_lock_automatically_expires_after_fifteen_minutes(self):
        user = User.objects.create_user(username="locked123", password="correct-password")
        for _ in range(5):
            self.client.post(reverse("login"), {"username": "locked123", "password": "wrong-password"})
        AccessAttempt.objects.filter(username="locked123").update(
            attempt_time=timezone.now() - timedelta(minutes=16)
        )

        response = self.client.post(
            reverse("login"),
            {"username": "locked123", "password": "correct-password"},
        )

        self.assertRedirects(response, reverse("home"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_lockout_for_one_source_ip_does_not_lock_another_source_ip(self):
        user = User.objects.create_user(username="locked123", password="correct-password")
        for _ in range(5):
            self.client.post(
                reverse("login"),
                {"username": "locked123", "password": "wrong-password"},
                REMOTE_ADDR="192.0.2.10",
            )

        response = self.client.post(
            reverse("login"),
            {"username": "locked123", "password": "correct-password"},
            REMOTE_ADDR="192.0.2.11",
        )

        self.assertRedirects(response, reverse("home"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)


class CustomerAccountIsolationTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username="abc123", password="customer-password")
        self.account = Account.objects.create(
            user=self.customer,
            first_name="Alex",
            last_name="Student",
            must_change_password=False,
        )
        self.other_user = User.objects.create_user(username="xyz789", password="other-password")
        self.other_account = Account.objects.create(
            user=self.other_user,
            first_name="Other",
            last_name="Student",
            must_change_password=False,
        )
        self.item = InventoryItem.objects.create(
            name="Coke",
            quantity_on_hand=10,
            member_price="1.25",
            non_member_price="1.50",
        )
        self.client.force_login(self.customer)

    def test_customer_account_detail_ignores_another_account_id(self):
        response = self.client.get(reverse("account-detail-staff", args=[self.other_account.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["account"], self.account)
        self.assertNotContains(response, "Other Student")

    def test_customer_sale_ignores_forged_account_id(self):
        response = self.client.post(
            reverse("new-sale"),
            {
                "account": str(self.other_account.pk),
                "item_1": str(self.item.pk),
                "quantity_1": "1",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Insufficient student balance")
        self.assertEqual(self.other_account.sales.count(), 0)
        self.assertEqual(self.account.sales.count(), 0)
