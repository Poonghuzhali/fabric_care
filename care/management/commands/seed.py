import shutil
from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.db import transaction
from PIL import Image, ImageFilter

from care.models import (
    AboutFeature,
    AboutSection,
    Booking,
    CallToAction,
    ContactMessage,
    CtaPoint,
    DifferenceItem,
    HeroSlide,
    NavLink,
    ProcessStep,
    SectionIntro,
    Service,
    SiteSetting,
    Testimonial,
)

ROOT = Path(__file__).resolve().parents[3]
IMAGES = ROOT / "Images"

HERO_TITLE = "Expert Care for\nEvery Fabric"
HERO_SUBTITLE = (
    "Professional saree care, ironing, steaming and finishing — handled "
    "with care and precision."
)

SERVICE_ROWS = [
    (
        "Saree Rolling",
        "Image (Saree Rolling).png",
        "Neat and professional rolling for easy storage and handling.",
        "Sarees are rolled along the length, with the border aligned and the pallu protected, so they store without a hard crease.",
        "30 min",
        "60.00",
        True,
    ),
    (
        "Towel Ironing & Refreshing",
        "Image (Towel Ironing & Refreshing).png",
        "Fresh, neat and comfortable finishing for towels.",
        "Towels are refreshed, pressed lightly and stacked square, without the flat, scorched finish of a heavy iron.",
        "25 min",
        "20.00",
        True,
    ),
    (
        "Coat & Delicate Fabric Steam Refresh",
        "Image (Coat & Delicate Fabric Steam Refresh).png",
        "Gentle steam treatment for coats and delicate fabrics.",
        "Coats, blends and delicate tailoring are steamed on the hanger so the shape returns and the surface stays soft.",
        "50 min",
        "150.00",
        True,
    ),
    (
        "Cotton Veshti Starching & Polishing",
        "Image (Cotton Veshti Starching & Polishing).png",
        "Crisp starching and polished finishing for cotton veshti.",
        "Cotton veshtis are given a light starch and a slow polish so the cloth is crisp and the zari border lies flat.",
        "40 min",
        "80.00",
        True,
    ),
    (
        "Silk Veshti Polishing",
        "Image (Silk Veshti Polishing).png",
        "Careful polishing to maintain the premium silk appearance.",
        "Silk veshtis are polished at a gentle heat. The body stays supple and the border keeps its shine.",
        "45 min",
        "120.00",
        True,
    ),
    (
        "Bed Sheet & Cover Ironing",
        "Image (Bed Sheet & Cover Ironing).png",
        "Smooth and neatly finished bed sheets and covers.",
        "Bed sheets, duvet covers and pillowcases are ironed flat and folded to a neat stack.",
        "30 min",
        "40.00",
        True,
    ),
    (
        "Saree Pre-Pleating",
        "Image (Saree Pre-Pleating).png",
        "Ready-to-wear pre-pleating for convenient styling.",
        "Pleats are measured, pressed and secured for the occasion, so the saree can be worn without pinning at the last minute.",
        "90 min",
        "250.00",
        False,
    ),
    (
        "Saree Polishing",
        "Image (Saree Polishing).png",
        "Professional polishing to enhance the saree's finish and appearance.",
        "Silk and rich cotton sarees are polished by hand until the body is even and the border catches the light again.",
        "60 min",
        "150.00",
        False,
    ),
    (
        "Cotton Saree Starching & Polishing",
        "Image (Cotton Saree Starching & Polishing).png",
        "Crisp starching with a clean, polished finish.",
        "Cotton sarees receive just enough starch to hold a fall, then a polish that keeps the cloth breathable.",
        "50 min",
        "120.00",
        False,
    ),
    (
        "Saree Folding",
        "Image (Saree Folding).png",
        "Neat and careful folding for organized storage.",
        "Each saree is folded to a clean square with the border visible, ready for the cupboard or a gift box.",
        "20 min",
        "40.00",
        False,
    ),
]


def _source(name):
    path = IMAGES / name
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def _logo_path():
    matches = [path for path in IMAGES.iterdir() if path.suffix.lower() == ".png" and path.name.startswith("Iron")]
    if not matches:
        raise FileNotFoundError("Iron Me·Ka logo was not found in the Images folder.")
    return matches[0]


def _file(path, stored_name):
    folder, filename = stored_name.split("/", 1)
    if default_storage.exists(stored_name):
        default_storage.delete(stored_name)
    return ContentFile(path.read_bytes(), name=filename)


def _cover(image, width, height):
    scale = max(width / image.width, height / image.height)
    resized = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))), Image.Resampling.LANCZOS)
    left = max(0, (resized.width - width) // 2)
    top = max(0, (resized.height - height) // 2)
    cropped = resized.crop((left, top, left + width, top + height))
    return cropped.filter(ImageFilter.UnsharpMask(radius=1.2, percent=80, threshold=2))


def _neatly_finished():
    """Side-by-side finished stacks, matching the third hero photograph."""
    left = Image.open(_source("Image (Saree Folding).png")).convert("RGB")
    right = Image.open(_source("Image (Cotton Veshti Starching & Polishing).png")).convert("RGB")
    width, height = 2000, 820
    canvas = _cover(left, width, height)
    right_width = int(width * 0.56)
    right_image = _cover(right, right_width, height).convert("RGBA")
    mask = Image.new("L", (right_width, height), 255)
    ramp = Image.new("L", (220, 1))
    for column in range(220):
        ramp.putpixel((column, 0), int(255 * (column / 219) ** 1.3))
    mask.paste(ramp.resize((220, height)), (0, 0))
    right_image.putalpha(mask)
    canvas = canvas.convert("RGBA")
    canvas.paste(right_image, (width - right_width, 0), right_image)
    buffer = BytesIO()
    canvas.convert("RGB").save(buffer, format="JPEG", quality=92)
    if default_storage.exists("hero/neatly-finished.jpg"):
        default_storage.delete("hero/neatly-finished.jpg")
    return ContentFile(buffer.getvalue(), name="neatly-finished.jpg")


class Command(BaseCommand):
    help = "Load the Iron Me·Ka landing page content into SQLite."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Replace existing landing-page content.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if SiteSetting.objects.exists() and not options["reset"]:
            self._sync_media()
            self.stdout.write(
                "Landing page content is already loaded; media files were synced from Images/."
            )
            return
        if options["reset"]:
            self._clear()
        self._create()
        self.stdout.write(self.style.SUCCESS("Landing page content is ready."))

    def _sync_media(self):
        """Rebuild uploaded image files (Render deploys start with an empty media/ folder)."""
        site = SiteSetting.objects.first()
        if not site:
            return
        site.logo = _file(_logo_path(), "brand/logo.png")
        site.save(update_fields=["logo"])

        about = AboutSection.objects.first()
        if about:
            about.image = _file(_source("Image (Saree Pre-Pleating).png"), "about/studio.png")
            about.save(update_fields=["image"])

        slide_specs = [
            (1, "hero/saree-care.png", _source("Image (Saree Care).png"), False),
            (2, "hero/professional-ironing.png", _source("Image (Professional Ironing).png"), False),
            (3, "hero/neatly-finished.jpg", None, True),
        ]
        for order, stored, source, generated in slide_specs:
            slide = HeroSlide.objects.filter(order=order).first()
            if not slide:
                continue
            slide.image = _neatly_finished() if generated else _file(source, stored)
            slide.save(update_fields=["image"])

        for index, row in enumerate(SERVICE_ROWS, start=1):
            name, filename, _summary, _description, _duration, _price, _footer = row
            slug = name.lower().replace(" & ", "-").replace(" ", "-")
            service = Service.objects.filter(name=name).first() or Service.objects.filter(order=index).first()
            if not service:
                continue
            service.image = _file(_source(filename), f"services/{slug}.png")
            service.save(update_fields=["image"])

    def _clear(self):
        Booking.objects.all().delete()
        ContactMessage.objects.all().delete()
        HeroSlide.objects.all().delete()
        AboutFeature.objects.all().delete()
        AboutSection.objects.all().delete()
        Service.objects.all().delete()
        DifferenceItem.objects.all().delete()
        ProcessStep.objects.all().delete()
        Testimonial.objects.all().delete()
        CtaPoint.objects.all().delete()
        CallToAction.objects.all().delete()
        SectionIntro.objects.all().delete()
        NavLink.objects.all().delete()
        SiteSetting.objects.all().delete()
        for folder in ("brand", "hero", "about", "services"):
            path = ROOT / "media" / folder
            if path.exists():
                shutil.rmtree(path)

    def _create(self):
        SiteSetting.objects.create(
            brand_name="Vastra Care",
            tagline="Premium saree and fabric care",
            logo=_file(_logo_path(), "brand/logo.png"),
            phone="+91 9790263322",
            email="hello@vastracare.in",
            address="6 Vincent de Paul street, COLAS NAGAR, PONDICHERRY - 605001",
            hours="Mon–Sat 9:00 AM – 8:00 PM · Sun 10:00 AM – 2:00 PM",
            instagram_url="https://instagram.com/",
            facebook_url="https://facebook.com/",
            youtube_url="https://youtube.com/",
            whatsapp_url="https://wa.me/919790263322",
            footer_blurb=(
                "Premium saree and fabric care — rolling, pleating, polishing, starching and steaming, "
                "done by hand with precision."
            ),
            copyright_text="© 2026 Vastra Care. All rights reserved.",
            slide_seconds=5,
        )

        links = [
            ("Home", "#home", 1),
            ("About Us", "#about", 2),
            ("Services", "#services", 3),
            ("Why Choose Us", "#difference", 4),
            ("Reviews", "#testimonials", 5),
            ("Contact", "#contact", 6),
        ]
        for label, url, order in links:
            NavLink.objects.create(label=label, url=url, order=order)

        slides = [
            ("SAREE CARE", "hero/saree-care.png", _source("Image (Saree Care).png"), 1),
            ("PROFESSIONAL IRONING", "hero/professional-ironing.png", _source("Image (Professional Ironing).png"), 2),
            ("NEATLY FINISHED", "hero/neatly-finished.jpg", None, 3),
        ]
        for eyebrow, stored, source, order in slides:
            image = _neatly_finished() if source is None else _file(source, stored)
            HeroSlide.objects.create(
                eyebrow=eyebrow,
                title=HERO_TITLE,
                subtitle=HERO_SUBTITLE,
                image=image,
                primary_label="Book a Service",
                primary_url="#book",
                secondary_label="View Services",
                secondary_url="#services",
                order=order,
            )

        AboutSection.objects.create(
            eyebrow="ABOUT US",
            heading="Care That Makes Every Fabric Feel Special",
            paragraph_one=(
                "At Vastra Care, we understand that traditional wear — especially silk sarees and veshtis — "
                "deserves more than a routine press. Each piece is handled manually, with attention to pleats, "
                "borders, zari and fall."
            ),
            paragraph_two=(
                "From rolling and pre-pleating to polishing and starching, our finishing is measured and careful, "
                "so your clothes return neat, fresh and ready to wear."
            ),
            image=_file(_source("Image (Saree Pre-Pleating).png"), "about/studio.png"),
            image_alt="Traditional fabric care and saree pleating",
            badge_value="12+",
            badge_label="YEARS OF CARE",
        )
        features = [
            ("medal", "Quality Finishing", "", 1),
            ("feather", "Gentle Fabric Care", "", 2),
            ("hand", "Professional Handling", "", 3),
        ]
        for icon, title, text, order in features:
            AboutFeature.objects.create(icon=icon, title=title, text=text, order=order)

        SectionIntro.objects.create(
            key="services",
            eyebrow="WHAT WE DO",
            heading="Our Fabric Care Services",
            subheading="Specialized care and finishing for your everyday wear and traditional fabrics.",
        )
        SectionIntro.objects.create(
            key="difference",
            eyebrow="WHY CHOOSE US",
            heading="The Vastra Care Difference",
            subheading="",
        )
        SectionIntro.objects.create(
            key="process",
            eyebrow="HOW IT WORKS",
            heading="Simple, Careful, Complete",
            subheading="",
        )
        SectionIntro.objects.create(
            key="testimonials",
            eyebrow="TESTIMONIALS",
            heading="Loved by Our Customers",
            subheading="",
        )

        for index, row in enumerate(SERVICE_ROWS, start=1):
            name, filename, summary, description, duration, price, footer = row
            slug = name.lower().replace(" & ", "-").replace(" ", "-")
            Service.objects.create(
                name=name,
                summary=summary,
                description=description,
                image=_file(_source(filename), f"services/{slug}.png"),
                duration=duration,
                price=price,
                order=index,
                show_in_footer=footer,
            )

        differences = [
            ("shield", "Professional Fabric Care", "Every fabric receives appropriate care.", 1),
            ("flower", "Specialized Saree Care", "Dedicated finishing for sarees and traditional wear.", 2),
            ("feather", "Delicate Fabric Handling", "Careful treatment for premium and delicate materials.", 3),
            ("medal", "Neat Premium Finish", "Consistent, clean and polished results.", 4),
        ]
        for icon, title, text, order in differences:
            DifferenceItem.objects.create(icon=icon, title=title, text=text, order=order)

        steps = [
            (1, "clipboard", "Choose Your Service", "Select the service you need."),
            (2, "hand", "Hand Over Your Clothes", "Give us your garments for professional care."),
            (3, "wand", "Expert Care & Finishing", "Our team carefully handles and finishes them."),
            (4, "check", "Ready to Wear", "Receive your fresh, neat and beautifully finished clothes."),
        ]
        for number, icon, title, text in steps:
            ProcessStep.objects.create(number=number, icon=icon, title=title, text=text, order=number)

        quotes = [
            (
                "Lakshmi R.",
                "Verified customer",
                "My Kanjivaram silks came back beautifully polished and rolled. They treat every saree like it's their own.",
            ),
            (
                "Arun Kumar",
                "Verified customer",
                "The silk veshti polishing for my wedding was flawless. Crisp, shining and on time.",
            ),
            (
                "Priya S.",
                "Verified customer",
                "Pre-pleating has saved me so much time before functions. Perfect pleats every single time!",
            ),
            (
                "Meena V.",
                "Verified customer",
                "Gentle with delicate fabrics and very professional. My go-to for all traditional wear.",
            ),
        ]
        for index, (name, city, quote) in enumerate(quotes, start=1):
            Testimonial.objects.create(name=name, city=city, quote=quote, rating=5, order=index)

        CallToAction.objects.create(
            eyebrow="BOOK TODAY",
            heading="Give Your Clothes the Care They Deserve",
            text=(
                "From everyday ironing to delicate saree and traditional wear care, "
                "we make every piece look its best."
            ),
            button_label="Book a Service",
            button_url="#book",
            link_label="WhatsApp Us",
            link_url="https://wa.me/919790263322",
        )
