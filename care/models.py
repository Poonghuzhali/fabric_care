import re

from django.core.exceptions import ValidationError
from django.core.validators import (
    FileExtensionValidator,
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models
from django.utils.deconstruct import deconstructible

from .public_site import is_public_nav_url

ALLOWED_IMAGE_EXTENSIONS = ("jpg", "jpeg", "png", "webp")
_image_validators = [FileExtensionValidator(allowed_extensions=ALLOWED_IMAGE_EXTENSIONS)]


@deconstructible
class MaxImageSizeValidator:
    """Reject uploads larger than max_bytes (default 5 MB)."""

    def __init__(self, max_bytes: int = 5 * 1024 * 1024):
        self.max_bytes = max_bytes

    def __call__(self, value):
        if value.size > self.max_bytes:
            raise ValidationError(
                f"Image must be {self.max_bytes // (1024 * 1024)} MB or smaller.",
                code="file_too_large",
            )

    def __eq__(self, other):
        return isinstance(other, MaxImageSizeValidator) and self.max_bytes == other.max_bytes


def validate_hex_color(value: str) -> None:
    if not (value or "").strip():
        return
    if not re.match(r"^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$", (value or "").strip()):
        raise ValidationError("Enter a valid hex colour such as #741f3f or #caa.")


class LandingPageSection(models.Model):
    """Reorderable middle sections (between hero and footer). Hero stays fixed at top."""

    SECTION_KEYS = [
        ("about", "About us"),
        ("services", "Services"),
        ("difference", "Why choose us"),
        ("process", "How it works"),
        ("testimonials", "Testimonials"),
        ("contact", "Contact / CTA"),
    ]

    key = models.CharField(max_length=30, choices=SECTION_KEYS, unique=True)
    order = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="Lower numbers appear earlier on the page.",
    )
    is_visible = models.BooleanField(default=True)
    extra_css_class = models.CharField(
        max_length=120,
        blank=True,
        help_text="Optional extra CSS classes for this section wrapper (advanced).",
    )
    background_color = models.CharField(
        max_length=12,
        blank=True,
        help_text="Optional section background (hex, e.g. #f9f3e9). Leave blank to use the theme default.",
        validators=[validate_hex_color],
    )
    background_image = models.ImageField(
        upload_to="section-bg/",
        blank=True,
        validators=_image_validators + [MaxImageSizeValidator()],
    )

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Landing page section"
        verbose_name_plural = "Landing page sections"

    def __str__(self):
        return dict(self.SECTION_KEYS).get(self.key, self.key)


class SiteSetting(models.Model):
    brand_name = models.CharField(max_length=80, default="Iron Me·Ka")
    tagline = models.CharField(max_length=160, blank=True)
    logo = models.ImageField(
        upload_to="brand/",
        blank=True,
        validators=_image_validators + [MaxImageSizeValidator()],
    )
    brand_fallback_text = models.CharField(
        max_length=12,
        blank=True,
        default="VC",
        help_text="Shown in the header when no logo image is uploaded.",
    )
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(
        blank=True,
        help_text="Shown on the site and used as the inbox for contact form messages (unless Enquiry inbox below is set).",
    )
    enquiry_inbox_email = models.EmailField(
        blank=True,
        help_text="Optional. If set, contact form submissions are emailed here instead of the main Email field.",
    )
    address = models.CharField(max_length=200, blank=True)
    hours = models.CharField(max_length=120, blank=True)
    instagram_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    whatsapp_url = models.URLField(blank=True)
    maps_url = models.URLField(
        blank=True,
        help_text="Optional Google Maps link (opens in a new tab from the contact area when set).",
    )
    footer_blurb = models.TextField(blank=True)
    copyright_text = models.CharField(max_length=180, blank=True)
    slide_seconds = models.PositiveSmallIntegerField(
        default=5,
        validators=[MinValueValidator(3), MaxValueValidator(20)],
        help_text="How long each hero picture zooms before the next one appears.",
    )
    hero_auto_advance = models.BooleanField(
        default=True,
        help_text="When off, slides change only with arrows or dots (interval still used for zoom animation).",
    )
    page_title_suffix = models.CharField(
        max_length=120,
        blank=True,
        default="— Expert Care for Every Fabric",
        help_text="Appended to the browser tab title on the public site.",
    )
    meta_description = models.TextField(
        blank=True,
        default=(
            "Professional saree care, ironing, steaming and finishing — handled with care and precision."
        ),
        help_text="Short summary for search engines (meta description).",
    )
    default_hero_title = models.TextField(
        blank=True,
        default="Expert Care for\nEvery Fabric",
        help_text="Shown when there are no active hero slides.",
    )
    default_hero_subtitle = models.TextField(blank=True, default="")
    nav_contact_label = models.CharField(
        max_length=60,
        blank=True,
        default="Book a Service",
        help_text="Primary button in the header (usually scrolls to contact).",
    )
    nav_contact_url = models.CharField(
        max_length=200,
        blank=True,
        default="#contact",
        help_text="Header CTA button link (e.g. #contact or tel:…).",
    )
    logo_max_height_px = models.PositiveSmallIntegerField(
        default=48,
        validators=[MinValueValidator(24), MaxValueValidator(120)],
        help_text="Logo height in the header and footer (pixels).",
    )
    header_sticky = models.BooleanField(
        default=True,
        help_text="Keep the navigation bar visible while scrolling.",
    )
    header_bg_color = models.CharField(
        max_length=12,
        blank=True,
        validators=[validate_hex_color],
        help_text="Header bar background (hex). Leave blank for default transparent/blend.",
    )
    header_text_color = models.CharField(
        max_length=12,
        blank=True,
        validators=[validate_hex_color],
        help_text="Main header text colour (hex).",
    )
    header_nav_link_color = models.CharField(
        max_length=12,
        blank=True,
        validators=[validate_hex_color],
        help_text="Navigation link colour (hex).",
    )
    header_nav_link_hover_color = models.CharField(
        max_length=12,
        blank=True,
        validators=[validate_hex_color],
        help_text="Navigation link hover/active colour (hex).",
    )
    header_cta_bg = models.CharField(
        max_length=12,
        blank=True,
        validators=[validate_hex_color],
        help_text="Header CTA button background (hex).",
    )
    header_cta_text_color = models.CharField(
        max_length=12,
        blank=True,
        validators=[validate_hex_color],
        help_text="Header CTA button text (hex).",
    )
    header_cta_hover_bg = models.CharField(
        max_length=12,
        blank=True,
        validators=[validate_hex_color],
        help_text="Header CTA button hover background (hex).",
    )
    footer_bg_color = models.CharField(
        max_length=12,
        blank=True,
        validators=[validate_hex_color],
        help_text="Footer background (hex).",
    )
    footer_text_color = models.CharField(
        max_length=12,
        blank=True,
        validators=[validate_hex_color],
        help_text="Footer text colour (hex).",
    )
    font_heading_family = models.CharField(
        max_length=200,
        blank=True,
        help_text='Google Fonts heading stack, e.g. "Cormorant Garamond", serif — leave blank for default.',
    )
    font_body_family = models.CharField(
        max_length=200,
        blank=True,
        help_text='Google Fonts body stack, e.g. "Mulish", sans-serif — leave blank for default.',
    )
    color_primary = models.CharField(
        max_length=12,
        blank=True,
        validators=[validate_hex_color],
        help_text="Primary brand colour (maroon by default).",
    )
    color_secondary = models.CharField(
        max_length=12,
        blank=True,
        validators=[validate_hex_color],
        help_text="Secondary / dark accent.",
    )
    color_accent = models.CharField(
        max_length=12,
        blank=True,
        validators=[validate_hex_color],
        help_text="Accent / gold highlights.",
    )
    color_page_background = models.CharField(
        max_length=12,
        blank=True,
        validators=[validate_hex_color],
        help_text="Page background (cream by default).",
    )
    color_heading_text = models.CharField(
        max_length=12,
        blank=True,
        validators=[validate_hex_color],
        help_text="Main heading text colour.",
    )
    color_body_text = models.CharField(
        max_length=12,
        blank=True,
        validators=[validate_hex_color],
        help_text="Body copy colour.",
    )
    button_bg_color = models.CharField(
        max_length=12,
        blank=True,
        validators=[validate_hex_color],
        help_text="Solid button background.",
    )
    button_text_color = models.CharField(
        max_length=12,
        blank=True,
        validators=[validate_hex_color],
        help_text="Solid button label colour.",
    )
    button_hover_bg_color = models.CharField(
        max_length=12,
        blank=True,
        validators=[validate_hex_color],
        help_text="Solid button hover background.",
    )
    heading_size_scale = models.PositiveSmallIntegerField(
        default=100,
        validators=[MinValueValidator(80), MaxValueValidator(130)],
        help_text="Scale main headings (% of design default).",
    )
    body_size_scale = models.PositiveSmallIntegerField(
        default=100,
        validators=[MinValueValidator(80), MaxValueValidator(130)],
        help_text="Scale body text (% of design default).",
    )
    border_radius_px = models.PositiveSmallIntegerField(
        default=18,
        validators=[MinValueValidator(0), MaxValueValidator(48)],
        help_text="Card and button corner radius (px).",
    )
    section_spacing_px = models.PositiveSmallIntegerField(
        default=72,
        validators=[MinValueValidator(32), MaxValueValidator(160)],
        help_text="Vertical padding for band sections (px).",
    )
    container_max_width_px = models.PositiveSmallIntegerField(
        default=1160,
        validators=[MinValueValidator(960), MaxValueValidator(1400)],
        help_text="Max content width (px).",
    )
    service_read_more_label = models.CharField(
        max_length=40,
        blank=True,
        default="Read more",
        help_text="Shown on each service card (opens detail).",
    )
    footer_quick_links_heading = models.CharField(max_length=80, blank=True, default="Quick Links")
    footer_services_heading = models.CharField(max_length=80, blank=True, default="Services")
    footer_contact_heading = models.CharField(max_length=80, blank=True, default="Contact")
    footer_enquiry_button_label = models.CharField(max_length=80, blank=True, default="Email enquiry")
    contact_label_phone = models.CharField(max_length=30, blank=True, default="PHONE")
    contact_label_whatsapp = models.CharField(max_length=30, blank=True, default="WHATSAPP")
    contact_label_email = models.CharField(max_length=30, blank=True, default="EMAIL")
    contact_label_address = models.CharField(max_length=30, blank=True, default="ADDRESS")
    contact_label_business_hours = models.CharField(max_length=40, blank=True, default="BUSINESS HOURS")
    cta_email_button_label = models.CharField(max_length=80, blank=True, default="Email us")
    contact_modal_eyebrow = models.CharField(max_length=60, blank=True, default="Contact")
    contact_modal_title = models.CharField(max_length=120, blank=True, default="Send us an email")
    contact_field_label_name = models.CharField(max_length=40, blank=True, default="Name")
    contact_field_label_phone = models.CharField(max_length=40, blank=True, default="Phone")
    contact_field_label_email = models.CharField(max_length=60, blank=True, default="Your email")
    contact_field_label_message = models.CharField(max_length=60, blank=True, default="Message")
    contact_field_placeholder_message = models.CharField(
        max_length=200, blank=True, default="Tell us what you need"
    )
    contact_submit_button_label = models.CharField(max_length=60, blank=True, default="Send email")
    contact_success_title = models.CharField(max_length=120, blank=True, default="Message sent")
    contact_success_message = models.TextField(
        blank=True,
        default="Thank you. Your message has reached the studio.",
        help_text="Shown after a successful contact form submission.",
    )
    contact_form_generic_error = models.CharField(
        max_length=200,
        blank=True,
        default="Something went wrong. Please try again.",
        help_text="Shown when the contact form response cannot be processed.",
    )
    contact_form_network_error = models.CharField(
        max_length=200,
        blank=True,
        default="Something went wrong. Please try again.",
        help_text="Shown when the browser cannot reach the server for the contact form.",
    )

    class Meta:
        verbose_name = "Site settings"
        verbose_name_plural = "Site settings"

    def __str__(self):
        return self.brand_name or "Site settings"

    def clean(self):
        super().clean()
        url = (self.nav_contact_url or "").strip()
        if url and not is_public_nav_url(url):
            raise ValidationError(
                {
                    "nav_contact_url": "Public site cannot link to Django admin. Use #contact, tel:, mailto:, or a safe URL."
                }
            )


class NavLink(models.Model):
    label = models.CharField(max_length=40)
    url = models.CharField(
        max_length=200,
        help_text="Use #about, #services, or a full URL. Do not use the Django admin path (/admin/); it is not shown on the public site.",
    )
    order = models.PositiveIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True)
    show_in_footer = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Navigation link"
        verbose_name_plural = "Navigation links"

    def __str__(self):
        return self.label

    def clean(self):
        super().clean()
        from .public_site import is_public_nav_label

        if not is_public_nav_label(self.label):
            raise ValidationError(
                {
                    "label": "Do not use the word 'admin' in public navigation labels. Open /admin/ only by typing the URL."
                }
            )
        if not is_public_nav_url(self.url):
            raise ValidationError(
                {"url": "Public navigation cannot link to Django admin. Use /admin only by typing the URL in the browser."}
            )


class HeroSlide(models.Model):
    eyebrow = models.CharField(max_length=40)
    title = models.CharField(
        max_length=120,
        help_text="Use a new line if the heading should break, for example Expert Care for / Every Fabric.",
    )
    subtitle = models.TextField()
    image = models.ImageField(upload_to="hero/", validators=_image_validators + [MaxImageSizeValidator()])
    image_position_x = models.CharField(
        max_length=12,
        blank=True,
        default="50%",
        help_text="Horizontal position of the image in the frame (CSS), e.g. 50% or 30%.",
    )
    image_position_y = models.CharField(
        max_length=12,
        blank=True,
        default="50%",
        help_text="Vertical position of the image (CSS), e.g. 50% or 20%.",
    )
    overlay_opacity = models.PositiveSmallIntegerField(
        default=40,
        validators=[MinValueValidator(0), MaxValueValidator(90)],
        help_text="Dark overlay strength over the image (0–90; higher = darker text backdrop).",
    )
    primary_label = models.CharField(max_length=40, default="Get in touch")
    primary_url = models.CharField(
        max_length=200,
        default="#contact",
        help_text="Use #contact to scroll to the contact section, or a full URL.",
    )
    secondary_label = models.CharField(max_length=40, default="Our services")
    secondary_url = models.CharField(max_length=200, default="#services")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Hero slide"
        verbose_name_plural = "Hero slides"

    def __str__(self):
        return self.eyebrow

    def clean(self):
        super().clean()
        for fname in ("primary_url", "secondary_url"):
            u = (getattr(self, fname) or "").strip()
            if u and not is_public_nav_url(u):
                raise ValidationError({fname: "Use a safe public URL (not Django admin)."})


class AboutSection(models.Model):
    eyebrow = models.CharField(max_length=40, default="Our story")
    heading = models.CharField(max_length=140)
    paragraph_one = models.TextField()
    paragraph_two = models.TextField(blank=True)
    image = models.ImageField(
        upload_to="about/",
        blank=True,
        validators=_image_validators + [MaxImageSizeValidator()],
    )
    image_alt = models.CharField(max_length=140, blank=True)
    badge_value = models.CharField(max_length=20, default="12+")
    badge_label = models.CharField(max_length=40, default="Years of care")
    button_label = models.CharField(max_length=60, blank=True)
    button_url = models.CharField(max_length=200, blank=True)
    section_bg_color = models.CharField(
        max_length=12,
        blank=True,
        validators=[validate_hex_color],
    )
    section_text_color = models.CharField(
        max_length=12,
        blank=True,
        validators=[validate_hex_color],
    )
    is_visible = models.BooleanField(default=True)

    class Meta:
        verbose_name = "About section"
        verbose_name_plural = "About section"

    def __str__(self):
        return self.heading

    def clean(self):
        super().clean()
        u = (self.button_url or "").strip()
        if u and not is_public_nav_url(u):
            raise ValidationError({"button_url": "Use a safe public URL (not Django admin)."})


class AboutFeature(models.Model):
    ICONS = [
        ("loom", "Fabric"),
        ("hand", "Hand"),
        ("door", "Doorstep"),
        ("spark", "Spark"),
        ("shield", "Shield"),
        ("steam", "Steam"),
        ("fold", "Fold"),
        ("medal", "Medal"),
        ("feather", "Feather"),
        ("flower", "Flower"),
    ]
    icon = models.CharField(max_length=20, choices=ICONS, default="spark")
    title = models.CharField(max_length=60)
    text = models.CharField(max_length=120, blank=True)
    image = models.ImageField(
        upload_to="about/features/",
        blank=True,
        validators=_image_validators + [MaxImageSizeValidator()],
        help_text="Optional image instead of or alongside the icon.",
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "About feature"
        verbose_name_plural = "About features"

    def __str__(self):
        return self.title


class SectionIntro(models.Model):
    KEYS = [
        ("services", "Services"),
        ("difference", "Difference"),
        ("process", "How it works"),
        ("testimonials", "Testimonials"),
    ]
    key = models.CharField(max_length=30, choices=KEYS, unique=True)
    eyebrow = models.CharField(max_length=40)
    heading = models.CharField(max_length=140)
    subheading = models.CharField(max_length=220, blank=True)
    is_visible = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Section heading"
        verbose_name_plural = "Section headings"

    def __str__(self):
        return self.heading


class Service(models.Model):
    name = models.CharField(max_length=120)
    summary = models.CharField(max_length=180)
    description = models.TextField()
    category = models.CharField(max_length=80, blank=True)
    price_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Optional numeric price (shown with prefix below).",
    )
    price_prefix = models.CharField(
        max_length=40,
        blank=True,
        default="From ₹",
        help_text="Text before the price (e.g. From ₹, Fixed ₹).",
    )
    price_suffix = models.CharField(
        max_length=40,
        blank=True,
        help_text="Optional text after the price (e.g. / piece).",
    )
    book_button_label = models.CharField(max_length=60, blank=True, default="Order Now")
    book_button_url = models.CharField(
        max_length=500,
        blank=True,
        default="#contact",
        help_text="Booking link: #contact, WhatsApp URL, tel:, or https URL.",
    )
    image = models.ImageField(upload_to="services/", validators=_image_validators + [MaxImageSizeValidator()])
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    show_in_footer = models.BooleanField(default=False)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Service"
        verbose_name_plural = "Services"

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        u = (self.book_button_url or "").strip()
        if u and not is_public_nav_url(u):
            raise ValidationError({"book_button_url": "Use a safe public URL (not Django admin)."})


class DifferenceItem(models.Model):
    ICONS = AboutFeature.ICONS
    icon = models.CharField(max_length=20, choices=ICONS, default="spark")
    title = models.CharField(max_length=80)
    text = models.CharField(max_length=180)
    image = models.ImageField(
        upload_to="difference/",
        blank=True,
        validators=_image_validators + [MaxImageSizeValidator()],
        help_text="Optional image shown with this feature.",
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Difference point"
        verbose_name_plural = "Difference points"

    def __str__(self):
        return self.title


class ProcessStep(models.Model):
    ICONS = [
        ("clipboard", "Clipboard"),
        ("hand", "Hand"),
        ("wand", "Wand"),
        ("check", "Check"),
    ]
    number = models.PositiveSmallIntegerField(default=1)
    icon = models.CharField(max_length=20, choices=ICONS, default="clipboard")
    title = models.CharField(max_length=80)
    text = models.CharField(max_length=180)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "number", "id"]
        verbose_name = "Process step"
        verbose_name_plural = "Process steps"

    def __str__(self):
        return f"{self.number}. {self.title}"


class Testimonial(models.Model):
    name = models.CharField(max_length=80)
    city = models.CharField(max_length=80, blank=True)
    designation = models.CharField(max_length=120, blank=True)
    photo = models.ImageField(
        upload_to="testimonials/",
        blank=True,
        validators=_image_validators + [MaxImageSizeValidator()],
    )
    quote = models.TextField()
    rating = models.PositiveSmallIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Testimonial"
        verbose_name_plural = "Testimonials"

    def __str__(self):
        return self.name

    @property
    def initial(self):
        return (self.name[:1] or "I").upper()


class CallToAction(models.Model):
    eyebrow = models.CharField(max_length=40, default="Ready when you are")
    heading = models.CharField(max_length=140)
    text = models.TextField(blank=True)
    button_label = models.CharField(max_length=40, default="Call us")
    button_url = models.CharField(max_length=200, default="tel:")
    link_label = models.CharField(max_length=40, blank=True, default="WhatsApp")
    link_url = models.CharField(max_length=200, blank=True, default="#contact")
    secondary_button_label = models.CharField(max_length=60, blank=True)
    secondary_button_url = models.CharField(max_length=500, blank=True)
    background_color = models.CharField(
        max_length=12,
        blank=True,
        validators=[validate_hex_color],
    )
    background_image = models.ImageField(
        upload_to="cta-bg/",
        blank=True,
        validators=_image_validators + [MaxImageSizeValidator()],
    )
    is_visible = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Call to action"
        verbose_name_plural = "Call to action"

    def __str__(self):
        return self.heading

    def clean(self):
        super().clean()
        for field in ("button_url", "link_url", "secondary_button_url"):
            u = (getattr(self, field) or "").strip()
            if u and not is_public_nav_url(u):
                raise ValidationError(
                    {field: "Use a safe public URL (not Django admin)."}
                )


class CtaPoint(models.Model):
    number = models.PositiveSmallIntegerField(default=1)
    title = models.CharField(max_length=80)
    text = models.CharField(max_length=160, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "number", "id"]
        verbose_name = "Call to action point"
        verbose_name_plural = "Call to action points"

    def __str__(self):
        return f"{self.number}. {self.title}"


class ContactMessage(models.Model):
    name = models.CharField(max_length=80)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField()
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Contact message"
        verbose_name_plural = "Contact messages"

    def __str__(self):
        return f"{self.name} — {self.email}"
