import json

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from django.core import mail
from django.test import override_settings
from django.urls import reverse

from care.mail import _smtp_from_email
from care.models import ContactMessage, HeroSlide, Service, SiteSetting, Testimonial


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

    def test_legacy_book_url_redirects_home(self):
        response = self.client.get("/book/")
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)

    def test_confirmation_uses_smtp_from_not_studio_address(self):
        site = SiteSetting.objects.first()
        self.assertTrue(site and site.email)
        with self.settings(DEFAULT_FROM_EMAIL="sender@gmail.com", EMAIL_HOST_USER="sender@gmail.com"):
            from_email, reply_to = _smtp_from_email(site)
        self.assertEqual(from_email, "sender@gmail.com")
        self.assertEqual(reply_to, [site.email])

    def test_brevo_smtp_login_is_not_used_as_from_address(self):
        site = SiteSetting.objects.first()
        with self.settings(
            DEFAULT_FROM_EMAIL="orders@example.com",
            EMAIL_HOST_USER="c1a0e2001@smtp-brevo.com",
        ):
            from_email, _reply_to = _smtp_from_email(site)
        self.assertEqual(from_email, "orders@example.com")

    def test_customer_auth_urls_redirect_home(self):
        for path in (reverse("login"), reverse("register"), reverse("account")):
            r = self.client.get(path)
            self.assertRedirects(r, reverse("home"), fetch_redirect_response=False)

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
