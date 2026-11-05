from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date

from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse
from PIL import Image

from care.models import Service
from portal.accounts import PORTAL_ADMIN_EMAIL, PORTAL_ADMIN_PASSWORD, ensure_portal_admin


class PortalAuthTests(TestCase):
    def setUp(self):
        ensure_portal_admin()
        user = get_user_model().objects.get(username=PORTAL_ADMIN_EMAIL)
        user.set_password(PORTAL_ADMIN_PASSWORD)
        user.save()
        self.client = Client()

    def test_login_page_renders(self):
        response = self.client.get("/portal/login/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign in to the admin panel")

    def test_portal_redirects_when_logged_out(self):
        response = self.client.get("/portal/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/portal/login/", response.url)

    def test_portal_login_with_preset_credentials(self):
        response = self.client.post(
            "/portal/login/",
            {
                "username": PORTAL_ADMIN_EMAIL,
                "password": PORTAL_ADMIN_PASSWORD,
            },
        )
        self.assertRedirects(response, "/portal/")
        dashboard = self.client.get("/portal/")
        self.assertEqual(dashboard.status_code, 200)
        self.assertContains(dashboard, "Dashboard / Overview")

    def test_home_has_login_button(self):
        response = self.client.get("/")
        self.assertContains(response, "Login")
        self.assertContains(response, reverse("login"))


class PortalServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed")

    def setUp(self):
        ensure_portal_admin()
        user = get_user_model().objects.get(username=PORTAL_ADMIN_EMAIL)
        user.set_password(PORTAL_ADMIN_PASSWORD)
        user.save()
        self.client = Client()
        self.client.login(username=PORTAL_ADMIN_EMAIL, password=PORTAL_ADMIN_PASSWORD)

    def _png_file(self, name="updated-service.png"):
        buffer = BytesIO()
        Image.new("RGB", (120, 90), color=(116, 31, 63)).save(buffer, format="PNG")
        buffer.seek(0)
        return SimpleUploadedFile(name, buffer.read(), content_type="image/png")

    def test_staff_can_replace_service_image(self):
        service = Service.objects.get(name="Saree Rolling")
        old_image = service.image.name
        url = reverse("portal:service_edit", args=[service.pk])
        page = self.client.get(url)
        self.assertContains(page, "Service photo")
        self.assertContains(page, service.image.url)

        response = self.client.post(
            url,
            {
                "name": service.name,
                "summary": service.summary,
                "description": service.description,
                "duration": service.duration,
                "price": service.price,
                "order": service.order,
                "is_active": "on",
                "show_in_footer": "on",
                "image": self._png_file(),
            },
        )
        self.assertRedirects(response, reverse("portal:services"))
        service.refresh_from_db()
        self.assertTrue(service.image.name)
        self.assertNotEqual(service.image.name, old_image)
        self.assertTrue(service.image.storage.exists(service.image.name))


class PortalCleanupTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed")

    def setUp(self):
        ensure_portal_admin()
        user = get_user_model().objects.get(username=PORTAL_ADMIN_EMAIL)
        user.set_password(PORTAL_ADMIN_PASSWORD)
        user.save()
        self.client.login(username=PORTAL_ADMIN_EMAIL, password=PORTAL_ADMIN_PASSWORD)

    def test_customers_page_loads(self):
        response = self.client.get(reverse("portal:customers"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Customers")

    def test_staff_can_delete_customer_and_bookings(self):
        customer = get_user_model().objects.create_user(
            username="remove.me@example.com",
            email="remove.me@example.com",
            password="CustomerPass123!",
        )
        from care.models import Booking, CustomerProfile

        CustomerProfile.objects.create(
            user=customer,
            full_name="Remove Me",
            phone="9000000001",
        )
        Booking.objects.create(
            customer=customer,
            name="Remove Me",
            phone="9000000001",
            email="remove.me@example.com",
            service_name="Saree Rolling",
            preferred_date=date(2026, 12, 1),
        )
        response = self.client.post(
            reverse("portal:customer_delete"),
            {"email": "remove.me@example.com"},
        )
        self.assertRedirects(response, reverse("portal:customers"))
        self.assertFalse(Booking.objects.filter(email="remove.me@example.com").exists())
        self.assertFalse(get_user_model().objects.filter(email="remove.me@example.com").exists())
