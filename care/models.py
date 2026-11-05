from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class SiteSetting(models.Model):
    brand_name = models.CharField(max_length=80, default="Iron Me·Ka")
    tagline = models.CharField(max_length=160, blank=True)
    logo = models.ImageField(upload_to="brand/", blank=True)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=200, blank=True)
    hours = models.CharField(max_length=120, blank=True)
    instagram_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    whatsapp_url = models.URLField(blank=True)
    footer_blurb = models.TextField(blank=True)
    copyright_text = models.CharField(max_length=180, blank=True)
    slide_seconds = models.PositiveSmallIntegerField(
        default=5,
        validators=[MinValueValidator(3), MaxValueValidator(20)],
        help_text="How long each hero picture zooms before the next one appears.",
    )

    class Meta:
        verbose_name = "Site settings"
        verbose_name_plural = "Site settings"

    def __str__(self):
        return self.brand_name or "Site settings"


class NavLink(models.Model):
    label = models.CharField(max_length=40)
    url = models.CharField(max_length=200, help_text="Use #about, #services, or a full address.")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    show_in_footer = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Navigation link"
        verbose_name_plural = "Navigation links"

    def __str__(self):
        return self.label


class HeroSlide(models.Model):
    eyebrow = models.CharField(max_length=40)
    title = models.CharField(
        max_length=120,
        help_text="Use a new line if the heading should break, for example Expert Care for / Every Fabric.",
    )
    subtitle = models.TextField()
    image = models.ImageField(upload_to="hero/")
    primary_label = models.CharField(max_length=40, default="Book a Service")
    primary_url = models.CharField(max_length=200, default="#book")
    secondary_label = models.CharField(max_length=40, default="View Services")
    secondary_url = models.CharField(max_length=200, default="#services")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Hero slide"
        verbose_name_plural = "Hero slides"

    def __str__(self):
        return self.eyebrow


class AboutSection(models.Model):
    eyebrow = models.CharField(max_length=40, default="Our story")
    heading = models.CharField(max_length=140)
    paragraph_one = models.TextField()
    paragraph_two = models.TextField(blank=True)
    image = models.ImageField(upload_to="about/", blank=True)
    image_alt = models.CharField(max_length=140, blank=True)
    badge_value = models.CharField(max_length=20, default="12+")
    badge_label = models.CharField(max_length=40, default="Years of care")

    class Meta:
        verbose_name = "About section"
        verbose_name_plural = "About section"

    def __str__(self):
        return self.heading


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

    class Meta:
        verbose_name = "Section heading"
        verbose_name_plural = "Section headings"

    def __str__(self):
        return self.heading


class Service(models.Model):
    name = models.CharField(max_length=120)
    summary = models.CharField(max_length=180)
    description = models.TextField()
    image = models.ImageField(upload_to="services/")
    duration = models.CharField(max_length=40, default="45 min")
    price = models.DecimalField(max_digits=8, decimal_places=2)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    show_in_footer = models.BooleanField(default=False)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Service"
        verbose_name_plural = "Services"

    def __str__(self):
        return self.name


class DifferenceItem(models.Model):
    ICONS = AboutFeature.ICONS
    icon = models.CharField(max_length=20, choices=ICONS, default="spark")
    title = models.CharField(max_length=80)
    text = models.CharField(max_length=180)
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
    button_label = models.CharField(max_length=40, default="Book a Service")
    button_url = models.CharField(max_length=200, default="#book")
    link_label = models.CharField(max_length=40, blank=True, default="Send a message")
    link_url = models.CharField(max_length=200, blank=True, default="#contact")

    class Meta:
        verbose_name = "Call to action"
        verbose_name_plural = "Call to action"

    def __str__(self):
        return self.heading


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


class RegistrationVerification(models.Model):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=80)
    phone = models.CharField(max_length=20)
    password_hash = models.CharField(max_length=128)
    otp_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Registration verification"
        verbose_name_plural = "Registration verifications"

    def __str__(self):
        return f"OTP pending — {self.email}"


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_profile",
    )
    full_name = models.CharField(max_length=80)
    phone = models.CharField(max_length=20)

    class Meta:
        verbose_name = "Customer profile"
        verbose_name_plural = "Customer profiles"

    def __str__(self):
        return self.full_name or self.user.email


class CustomerAddress(models.Model):
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_addresses",
    )
    label = models.CharField(max_length=40, blank=True, default="")
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    maps_url = models.URLField(max_length=500, blank=True, default="")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_default", "-updated_at", "-id"]
        verbose_name = "Customer address"
        verbose_name_plural = "Customer addresses"

    def __str__(self):
        return f"{self.display_label()} — {self.customer_id}"

    def display_label(self):
        if self.label.strip():
            return self.label.strip()
        short = self.address.strip()
        if len(short) > 36:
            short = short[:33] + "…"
        return short or "Saved address"


class Booking(models.Model):
    STATUS = [
        ("new", "New"),
        ("confirmed", "Confirmed"),
        ("in_care", "In care"),
        ("ready", "Ready"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="bookings",
    )
    name = models.CharField(max_length=80)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    service = models.ForeignKey(
        Service,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="bookings",
    )
    service_name = models.CharField(max_length=120)
    preferred_date = models.DateField()
    pickup_address = models.TextField(blank=True, default="")
    pickup_latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    pickup_longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    pickup_maps_url = models.URLField(max_length=500, blank=True, default="")
    notes = models.TextField(blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_order_id = models.CharField(max_length=80, blank=True, default="")
    payment_id = models.CharField(max_length=80, blank=True, null=True, unique=True)
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ("unpaid", "Unpaid"),
            ("paid", "Paid"),
            ("failed", "Failed"),
        ],
        default="unpaid",
    )
    status = models.CharField(max_length=20, choices=STATUS, default="new")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"

    def __str__(self):
        return f"{self.name} — {self.service_name}"


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
