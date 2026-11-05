from django.contrib import admin
from django.utils.html import format_html

from .models import (
    AboutFeature,
    AboutSection,
    Booking,
    CallToAction,
    ContactMessage,
    CustomerProfile,
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


def image_preview(obj, field="image"):
    image = getattr(obj, field, None)
    if image:
        return format_html(
            '<img src="{}" alt="" style="height:48px;width:72px;object-fit:cover;border-radius:8px;" />',
            image.url,
        )
    return "—"


class SingletonAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)


@admin.register(SiteSetting)
class SiteSettingAdmin(SingletonAdmin):
    fieldsets = (
        ("Brand", {"fields": ("brand_name", "tagline", "logo", "slide_seconds")}),
        ("Contact", {"fields": ("phone", "email", "address", "hours")}),
        ("Social", {"fields": ("instagram_url", "facebook_url", "youtube_url", "whatsapp_url")}),
        ("Footer", {"fields": ("footer_blurb", "copyright_text")}),
    )

    def logo_preview(self, obj):
        return image_preview(obj, "logo")

    readonly_fields = ()

    def changelist_view(self, request, extra_context=None):
        return super().changelist_view(request, extra_context)


@admin.register(NavLink)
class NavLinkAdmin(admin.ModelAdmin):
    list_display = ("label", "url", "order", "is_active", "show_in_footer")
    list_editable = ("order", "is_active", "show_in_footer")
    search_fields = ("label", "url")
    list_filter = ("is_active", "show_in_footer")


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ("preview", "eyebrow", "title", "order", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("eyebrow", "title", "subtitle")
    list_filter = ("is_active",)
    ordering = ("order", "id")
    fieldsets = (
        (
            None,
            {
                "description": (
                    "These slides sit under the menu. Each picture zooms in for the "
                    "number of seconds set in Site settings, then the next slide appears. "
                    "The sequence repeats."
                ),
                "fields": (
                    "eyebrow",
                    "title",
                    "subtitle",
                    "image",
                    "order",
                    "is_active",
                ),
            },
        ),
        ("Buttons", {"fields": ("primary_label", "primary_url", "secondary_label", "secondary_url")}),
    )

    @admin.display(description="Image")
    def preview(self, obj):
        return image_preview(obj)


@admin.register(AboutSection)
class AboutSectionAdmin(SingletonAdmin):
    fieldsets = (
        ("Text", {"fields": ("eyebrow", "heading", "paragraph_one", "paragraph_two")}),
        ("Photograph", {"fields": ("image", "image_alt", "badge_value", "badge_label")}),
    )


@admin.register(AboutFeature)
class AboutFeatureAdmin(admin.ModelAdmin):
    list_display = ("title", "icon", "text", "order", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("title", "text")
    list_filter = ("is_active", "icon")


@admin.register(SectionIntro)
class SectionIntroAdmin(admin.ModelAdmin):
    list_display = ("key", "eyebrow", "heading", "subheading")
    search_fields = ("heading", "subheading", "eyebrow")
    list_filter = ("key",)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("preview", "name", "price", "duration", "order", "is_active", "show_in_footer")
    list_editable = ("price", "duration", "order", "is_active", "show_in_footer")
    search_fields = ("name", "summary", "description")
    list_filter = ("is_active", "show_in_footer")
    ordering = ("order", "id")

    @admin.display(description="Image")
    def preview(self, obj):
        return image_preview(obj)


@admin.register(DifferenceItem)
class DifferenceItemAdmin(admin.ModelAdmin):
    list_display = ("title", "icon", "text", "order", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("title", "text")
    list_filter = ("is_active",)


@admin.register(ProcessStep)
class ProcessStepAdmin(admin.ModelAdmin):
    list_display = ("title", "number", "text", "order", "is_active")
    list_editable = ("number", "order", "is_active")
    search_fields = ("title", "text")
    list_filter = ("is_active",)


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "rating", "order", "is_active")
    list_editable = ("rating", "order", "is_active")
    search_fields = ("name", "city", "quote")
    list_filter = ("is_active", "rating")


@admin.register(CallToAction)
class CallToActionAdmin(SingletonAdmin):
    fieldsets = (
        ("Banner", {"fields": ("eyebrow", "heading", "text")}),
        ("Actions", {"fields": ("button_label", "button_url", "link_label", "link_url")}),
    )


@admin.register(CtaPoint)
class CtaPointAdmin(admin.ModelAdmin):
    list_display = ("title", "number", "text", "order", "is_active")
    list_editable = ("number", "order", "is_active")
    search_fields = ("title", "text")
    list_filter = ("is_active",)


@admin.action(description="Mark selected bookings as confirmed")
def mark_bookings_confirmed(modeladmin, request, queryset):
    queryset.update(status="confirmed")


@admin.action(description="Mark selected bookings as completed")
def mark_bookings_completed(modeladmin, request, queryset):
    queryset.update(status="completed")


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "user")
    search_fields = ("full_name", "phone", "user__email", "user__username")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("name", "service_name", "customer", "phone", "preferred_date", "status", "created_at")
    list_filter = ("status", "preferred_date", "service")
    search_fields = ("name", "phone", "email", "service_name", "notes")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)
    actions = (mark_bookings_confirmed, mark_bookings_completed)
    fieldsets = (
        ("Guest", {"fields": ("customer", "name", "phone", "email")}),
        (
            "Request",
            {
                "fields": (
                    "service",
                    "service_name",
                    "preferred_date",
                    "pickup_address",
                    "pickup_latitude",
                    "pickup_longitude",
                    "pickup_maps_url",
                    "notes",
                    "status",
                )
            },
        ),
        (
            "Payment",
            {
                "fields": (
                    "amount_paid",
                    "payment_status",
                    "payment_order_id",
                    "payment_id",
                )
            },
        ),
        ("Record", {"fields": ("created_at",)}),
    )


@admin.action(description="Mark selected messages as read")
def mark_messages_read(modeladmin, request, queryset):
    queryset.update(is_read=True)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "is_read", "created_at")
    list_filter = ("is_read",)
    search_fields = ("name", "email", "phone", "message")
    readonly_fields = ("created_at",)
    actions = (mark_messages_read,)
    date_hierarchy = "created_at"
