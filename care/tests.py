import json

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from care.mail import _smtp_from_email
from care.models import ContactMessage, HeroSlide, NavLink, Service, SiteSetting, Testimonial


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
        self.assertContains(response, "Pricing")
        self.assertContains(response, "How it Works")
        self.assertContains(response, "Reviews")
        self.assertContains(response, "GET IN TOUCH")
        self.assertContains(response, "Book a Service")
        self.assertContains(response, "Book Now")
        self.assertContains(response, "Our Services")
        self.assertContains(response, "Order Now")
        self.assertContains(response, "Simple, Careful, Complete")
        self.assertContains(response, "Loved by Our Customers")
        self.assertContains(response, "Give Your Clothes the Care They Deserve")
        self.assertContains(response, "Cormorant+Garamond")
        self.assertContains(response, "Mulish")
        # Theme CSS must set font stacks without an extra wrapping quote (breaks var(--serif))
        self.assertContains(response, '--serif: "Cormorant Garamond", serif;')
        self.assertContains(response, '--sans: "Mulish", sans-serif;')
        self.assertNotContains(response, '--serif: ""Cormorant Garamond"')
        self.assertNotContains(response, 'href="/admin/')
        self.assertNotContains(response, ">Admin</a>")
        self.assertNotContains(response, "Django admin")
        self.assertNotContains(response, "edit site content")
        self.assertContains(response, "SAREE CARE")
        self.assertContains(response, "PROFESSIONAL IRONING")
        self.assertContains(response, "NEATLY FINISHED")
        self.assertEqual(HeroSlide.objects.filter(is_active=True).count(), 3)
        self.assertEqual(Service.objects.filter(is_active=True).count(), 10)
        self.assertContains(response, 'style="--slide-time: 5s"')

    def test_public_nav_excludes_admin_links(self):
        NavLink.objects.create(
            label="Staff login",
            url="https://example.com/admin/",
            order=99,
            is_active=True,
            show_in_footer=True,
        )
        NavLink.objects.create(
            label="Admin",
            url="#admin",
            order=98,
            is_active=True,
            show_in_footer=True,
        )
        NavLink.objects.create(
            label="Site admin",
            url="#about",
            order=97,
            is_active=True,
            show_in_footer=True,
        )
        # CamelCase "admin" (no space before Admin) used to bypass \b-based checks
        NavLink.objects.create(
            label="SiteAdmin",
            url="#services",
            order=96,
            is_active=True,
            show_in_footer=True,
        )
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "https://example.com/admin/")
        self.assertNotContains(response, ">Admin</a>")
        self.assertNotContains(response, "Site admin")
        self.assertNotContains(response, "SiteAdmin")
        site = SiteSetting.objects.first()
        site.instagram_url = "https://admin.example.com/foo"
        site.save()
        response2 = self.client.get("/")
        self.assertEqual(response2.status_code, 200)
        self.assertNotContains(response2, "admin.example.com")
        link = NavLink(label="Bad", url="/admin/")
        with self.assertRaises(ValidationError):
            link.full_clean()

    def test_scrubs_booking_and_admin_footer_copy(self):
        site = SiteSetting.objects.first()
        site.copyright_text = "© Test — Django admin — edit site content"
        site.save()
        HeroSlide.objects.update(
            primary_label="Book now",
            primary_url="https://unsafe.example/book",
            secondary_label="Book tours",
            secondary_url="#x",
        )
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "unsafe.example")
        self.assertNotContains(response, "Django admin")
        self.assertNotContains(response, "edit site content")
        self.assertContains(response, "Book Now")

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
