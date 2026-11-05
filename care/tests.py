import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from django.core import mail
from django.test import override_settings
from django.urls import reverse

from django.conf import settings

from care.mail import _smtp_from_email
from care.models import Booking, ContactMessage, CustomerProfile, HeroSlide, Service, SiteSetting, Testimonial


def _sample_payment():
    return {
        "razorpay_order_id": "order_test_001",
        "razorpay_payment_id": "pay_test_001",
        "razorpay_signature": "test_signature",
    }


def _sample_pickup():
    return {
        "pickup_address": "12 Vincent de Paul Street, Colas Nagar, Puducherry 605001",
        "pickup_latitude": "11.913900",
        "pickup_longitude": "79.814500",
        "pickup_maps_url": "https://www.google.com/maps?q=11.9139,79.8145",
    }


class LandingPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed")

    def test_home_renders_design_content(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Expert Care for")
        self.assertContains(response, "Every Fabric")
        self.assertContains(response, "Our Fabric Care Services")
        self.assertContains(response, "The Vastra Care Difference")
        self.assertContains(response, "About Us")
        self.assertContains(response, "Why Choose Us")
        self.assertContains(response, "Reviews")
        self.assertContains(response, "BOOK TODAY")
        self.assertContains(response, "Book Now")
        self.assertContains(response, "Simple, Careful, Complete")
        self.assertContains(response, "Loved by Our Customers")
        self.assertContains(response, "Give Your Clothes the Care They Deserve")
        self.assertContains(response, "Cormorant+Garamond")
        self.assertContains(response, "Mulish")
        self.assertContains(response, "SAREE CARE")
        self.assertContains(response, "PROFESSIONAL IRONING")
        self.assertContains(response, "NEATLY FINISHED")
        self.assertEqual(HeroSlide.objects.filter(is_active=True).count(), 3)
        self.assertEqual(Service.objects.filter(is_active=True).count(), 10)
        self.assertContains(response, 'style="--slide-time: 5s"')

    def test_booking_requires_customer_login(self):
        service = Service.objects.first()
        when = (timezone.localdate() + timedelta(days=2)).isoformat()
        response = self.client.post(
            "/book/",
            data=json.dumps(
                {
                    "name": "Guest User",
                    "phone": "9840011122",
                    "email": "guest@example.com",
                    "service": service.id,
                    "preferred_date": when,
                    "notes": "",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("redirect", response.json())
        self.assertEqual(Booking.objects.count(), 0)

    def test_confirmation_uses_smtp_from_not_studio_address(self):
        site = SiteSetting.objects.first()
        self.assertTrue(site and site.email)
        with self.settings(DEFAULT_FROM_EMAIL="sender@gmail.com", EMAIL_HOST_USER="sender@gmail.com"):
            from_email, reply_to = _smtp_from_email(site)
        self.assertEqual(from_email, "sender@gmail.com")
        self.assertEqual(reply_to, [site.email])

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        EMAIL_HOST="smtp.gmail.com",
        EMAIL_HOST_USER="sender@gmail.com",
        EMAIL_HOST_PASSWORD="test-app-password",
        EMAIL_CONFIGURED=True,
        PAYMENT_SKIP_VERIFY=True,
        RAZORPAY_KEY_ID="test_key",
        RAZORPAY_KEY_SECRET="test_secret",
    )
    def test_booking_sends_confirmation_email(self):
        user = get_user_model().objects.create_user(
            username="mail@example.com",
            email="mail@example.com",
            password="CustomerPass123!",
        )
        CustomerProfile.objects.create(user=user, full_name="Mail User", phone="9840011122")
        self.client.login(username="mail@example.com", password="CustomerPass123!")
        service = Service.objects.first()
        when = (timezone.localdate() + timedelta(days=3)).isoformat()
        mail.outbox.clear()
        response = self.client.post(
            "/book/",
            data=json.dumps(
                {
                    "name": "Mail User",
                    "phone": "9840011122",
                    "email": "mail@example.com",
                    "service": service.id,
                    "preferred_date": when,
                    "notes": "Silk saree",
                    **_sample_pickup(),
                    **_sample_payment(),
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ["mail@example.com"])
        self.assertIn(service.name, message.subject)
        self.assertIn(service.name, message.body)
        self.assertIn("confirmation email was sent", response.json()["message"].lower())

    @override_settings(
        PAYMENT_SKIP_VERIFY=True,
        RAZORPAY_KEY_ID="test_key",
        RAZORPAY_KEY_SECRET="test_secret",
    )
    def test_booking_is_saved(self):
        user = get_user_model().objects.create_user(
            username="divya@example.com",
            email="divya@example.com",
            password="CustomerPass123!",
        )
        CustomerProfile.objects.create(user=user, full_name="Divya Nair", phone="9840011122")
        self.client.login(username="divya@example.com", password="CustomerPass123!")
        service = Service.objects.get(name="Saree Polishing")
        when = (timezone.localdate() + timedelta(days=2)).isoformat()
        response = self.client.post(
            "/book/",
            data=json.dumps(
                {
                    "name": "Divya Nair",
                    "phone": "9840011122",
                    "email": "divya@example.com",
                    "service": service.id,
                    "preferred_date": when,
                    "notes": "One maroon silk saree.",
                    **_sample_pickup(),
                    **_sample_payment(),
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        booking = Booking.objects.get(email="divya@example.com")
        self.assertEqual(booking.payment_status, "paid")
        self.assertIn("Colas Nagar", booking.pickup_address)
        self.assertEqual(str(booking.pickup_latitude), "11.913900")
        self.assertEqual(booking.service_name, "Saree Polishing")
        self.assertEqual(booking.status, "new")
        self.assertEqual(booking.customer_id, user.id)

    def test_customer_can_register_login_and_see_booking(self):
        response = self.client.post(
            reverse("register"),
            {
                "full_name": "Rahul Menon",
                "email": "rahul@example.com",
                "phone": "9800012345",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )
        self.assertRedirects(response, "/account/")
        account = self.client.get(reverse("account"))
        self.assertContains(account, "Track your orders")
        self.assertContains(account, "Rahul Menon")

    def test_customer_login_page_requires_credentials(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, "Sign in with your email and password")
        bad = self.client.post(reverse("login"), {"username": "nope@example.com", "password": "wrong"})
        self.assertEqual(bad.status_code, 200)
        self.assertContains(bad, "did not match")

    @override_settings(
        PAYMENT_SKIP_VERIFY=True,
        RAZORPAY_KEY_ID="test_key",
        RAZORPAY_KEY_SECRET="test_secret",
    )
    def test_booking_rejects_a_past_date(self):
        user = get_user_model().objects.create_user(
            username="past@example.com",
            email="past@example.com",
            password="CustomerPass123!",
        )
        CustomerProfile.objects.create(user=user, full_name="Past Date User", phone="9840011122")
        self.client.login(username="past@example.com", password="CustomerPass123!")
        service = Service.objects.first()
        response = self.client.post(
            "/book/",
            data=json.dumps(
                {
                    "name": "Past Date User",
                    "phone": "9840011122",
                    "email": "past@example.com",
                    "service": service.id,
                    "preferred_date": "2020-01-01",
                    "notes": "",
                    **_sample_pickup(),
                    **_sample_payment(),
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("preferred_date", response.json()["errors"])
        self.assertEqual(Booking.objects.count(), 0)

    @override_settings(RAZORPAY_KEY_ID="test_key", RAZORPAY_KEY_SECRET="test_secret")
    def test_booking_requires_payment_before_submit(self):
        user = get_user_model().objects.create_user(
            username="pay@example.com",
            email="pay@example.com",
            password="CustomerPass123!",
        )
        CustomerProfile.objects.create(user=user, full_name="Pay User", phone="9840011122")
        self.client.login(username="pay@example.com", password="CustomerPass123!")
        service = Service.objects.first()
        when = (timezone.localdate() + timedelta(days=2)).isoformat()
        response = self.client.post(
            "/book/",
            data=json.dumps(
                {
                    "name": "Pay User",
                    "phone": "9840011122",
                    "email": "pay@example.com",
                    "service": service.id,
                    "preferred_date": when,
                    "notes": "",
                    **_sample_pickup(),
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("form", response.json()["errors"])

    def test_booking_requires_pickup_map_pin(self):
        user = get_user_model().objects.create_user(
            username="map@example.com",
            email="map@example.com",
            password="CustomerPass123!",
        )
        CustomerProfile.objects.create(user=user, full_name="Map User", phone="9840011122")
        self.client.login(username="map@example.com", password="CustomerPass123!")
        service = Service.objects.first()
        when = (timezone.localdate() + timedelta(days=2)).isoformat()
        response = self.client.post(
            "/book/",
            data=json.dumps(
                {
                    "name": "Map User",
                    "phone": "9840011122",
                    "email": "map@example.com",
                    "service": service.id,
                    "preferred_date": when,
                    "pickup_address": "Short",
                    "notes": "",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        errors = response.json()["errors"]
        self.assertTrue("pickup_address" in errors or "pickup_latitude" in errors)

    def test_register_shows_password_validation_on_form(self):
        response = self.client.post(
            reverse("register"),
            {
                "full_name": "Weak Pass User",
                "email": "weak@example.com",
                "phone": "9800012345",
                "password1": "123",
                "password2": "123",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "has-error")
        self.assertContains(response, 'data-error-for="password1"')
        self.assertFalse(get_user_model().objects.filter(email="weak@example.com").exists())

    def test_contact_json_returns_field_errors(self):
        response = self.client.post(
            "/contact/",
            data=json.dumps(
                {
                    "name": "A",
                    "phone": "",
                    "email": "not-an-email",
                    "message": "short",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        errors = response.json()["errors"]
        self.assertIn("email", errors)
        self.assertIn("message", errors)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_contact_message_is_saved(self):
        response = self.client.post(
            "/contact/",
            data=json.dumps(
                {
                    "name": "Rahul Menon",
                    "phone": "9800012345",
                    "email": "rahul@example.com",
                    "message": "Do you polish tissue sarees?",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ContactMessage.objects.filter(email="rahul@example.com").exists())

    def test_admin_can_update_and_delete_a_testimonial(self):
        user = get_user_model().objects.create_superuser(
            "admin",
            "admin@ironmeka.example",
            "Admin@12345",
        )
        self.client.force_login(user)
        note = Testimonial.objects.create(
            name="Temporary Guest",
            city="Mysuru",
            quote="A short note for the admin test.",
            rating=4,
            order=20,
        )
        response = self.client.post(
            f"/admin/care/testimonial/{note.id}/change/",
            {
                "name": "Updated Guest",
                "city": "Mysuru",
                "quote": "Updated after a second visit.",
                "rating": 5,
                "order": 20,
                "is_active": "on",
                "_save": "Save",
            },
        )
        self.assertEqual(response.status_code, 302)
        note.refresh_from_db()
        self.assertEqual(note.name, "Updated Guest")
        delete = self.client.post(
            f"/admin/care/testimonial/{note.id}/delete/",
            {"post": "yes"},
        )
        self.assertEqual(delete.status_code, 302)
        self.assertFalse(Testimonial.objects.filter(pk=note.id).exists())

    def test_slide_images_exist(self):
        for slide in HeroSlide.objects.all():
            self.assertTrue(slide.image.name)
            self.assertTrue(slide.image.storage.exists(slide.image.name))
