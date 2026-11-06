from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    AboutFeature,
    AboutSection,
    CallToAction,
    ContactMessage,
    CtaPoint,
    DifferenceItem,
    HeroSlide,
    LandingPageSection,
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
        (
            "Brand & logo",
            {
                "fields": (
                    "brand_name",
                    "tagline",
                    "logo",
                    "brand_fallback_text",
                    "logo_max_height_px",
                )
            },
        ),
        (
            "SEO & page title",
            {
                "fields": ("page_title_suffix", "meta_description"),
                "description": "Browser tab title is: brand name + page title suffix.",
            },
        ),
        (
            "Hero (no slides)",
            {
                "fields": ("default_hero_title", "default_hero_subtitle"),
                "description": "Shown only when there are no active hero slides.",
            },
        ),
        (
            "Hero carousel",
            {
                "fields": ("slide_seconds", "hero_auto_advance"),
                "description": "Slide duration and whether slides advance automatically.",
            },
        ),
        (
            "Header & navigation",
            {
                "fields": (
                    "nav_contact_label",
                    "nav_contact_url",
                    "service_read_more_label",
                    "header_sticky",
                    "header_bg_color",
                    "header_text_color",
                    "header_nav_link_color",
                    "header_nav_link_hover_color",
                    "header_cta_bg",
                    "header_cta_text_color",
                    "header_cta_hover_bg",
                ),
            },
        ),
        (
            "Website appearance (colours & typography)",
            {
                "fields": (
                    "font_heading_family",
                    "font_body_family",
                    "color_primary",
                    "color_secondary",
                    "color_accent",
                    "color_page_background",
                    "color_heading_text",
                    "color_body_text",
                    "button_bg_color",
                    "button_text_color",
                    "button_hover_bg_color",
                    "heading_size_scale",
                    "body_size_scale",
                    "border_radius_px",
                    "section_spacing_px",
                    "container_max_width_px",
                ),
                "description": "Overrides default theme variables. Leave blank to keep the original Vastra Care palette.",
            },
        ),
        (
            "Footer appearance",
            {"fields": ("footer_bg_color", "footer_text_color")},
        ),
        (
            "Contact strip labels (PHONE, etc.)",
            {
                "fields": (
                    "contact_label_phone",
                    "contact_label_whatsapp",
                    "contact_label_email",
                    "contact_label_address",
                    "contact_label_business_hours",
                    "cta_email_button_label",
                ),
            },
        ),
        (
            "Contact modal & form",
            {
                "fields": (
                    "contact_modal_eyebrow",
                    "contact_modal_title",
                    "contact_field_label_name",
                    "contact_field_label_phone",
                    "contact_field_label_email",
                    "contact_field_label_message",
                    "contact_field_placeholder_message",
                    "contact_submit_button_label",
                    "contact_success_title",
                    "contact_success_message",
                    "contact_form_generic_error",
                    "contact_form_network_error",
                ),
                "description": "Success message here is the default; the live thank-you text also uses this after submit.",
            },
        ),
        (
            "Footer content",
            {
                "fields": (
                    "footer_quick_links_heading",
                    "footer_services_heading",
                    "footer_contact_heading",
                    "footer_enquiry_button_label",
                    "footer_blurb",
                    "copyright_text",
                ),
            },
        ),
        (
            "Contact details",
            {
                "fields": ("phone", "email", "enquiry_inbox_email", "address", "hours", "maps_url"),
                "description": "Contact form messages are emailed to Enquiry inbox if set, otherwise to Email.",
            },
        ),
        (
            "Social",
            {"fields": ("instagram_url", "facebook_url", "youtube_url", "whatsapp_url")},
        ),
    )


@admin.register(NavLink)
class NavLinkAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ("label", "url", "order", "is_active", "show_in_footer")
    list_editable = ("is_active", "show_in_footer")
    sortable_field_name = "order"
    search_fields = ("label", "url")
    list_filter = ("is_active", "show_in_footer")


@admin.register(HeroSlide)
class HeroSlideAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ("preview", "eyebrow", "title", "order", "is_active")
    list_editable = ("is_active",)
    sortable_field_name = "order"
    search_fields = ("eyebrow", "title", "subtitle")
    list_filter = ("is_active",)
    ordering = ("order", "id")
    fieldsets = (
        (
            None,
            {
                "description": (
                    "These slides sit under the menu. Each picture zooms in for the "
                    "number of seconds set in Site settings, then the next slide appears."
                ),
                "fields": (
                    "eyebrow",
                    "title",
                    "subtitle",
                    "image",
                    "image_position_x",
                    "image_position_y",
                    "overlay_opacity",
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
        ("Visibility", {"fields": ("is_visible",)}),
        ("Text", {"fields": ("eyebrow", "heading", "paragraph_one", "paragraph_two")}),
        ("Photograph", {"fields": ("image", "image_alt", "badge_value", "badge_label")}),
        ("Optional button", {"fields": ("button_label", "button_url")}),
        ("Section colours", {"fields": ("section_bg_color", "section_text_color")}),
    )


@admin.register(AboutFeature)
class AboutFeatureAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ("title", "icon", "image_thumb", "text", "order", "is_active")
    list_editable = ("is_active",)
    sortable_field_name = "order"
    search_fields = ("title", "text")
    list_filter = ("is_active", "icon")
    readonly_fields = ("image_thumb",)

    @admin.display(description="Image")
    def image_thumb(self, obj):
        return image_preview(obj, "image")


@admin.register(SectionIntro)
class SectionIntroAdmin(admin.ModelAdmin):
    list_display = ("key", "is_visible", "eyebrow", "heading", "subheading")
    list_editable = ("is_visible",)
    search_fields = ("heading", "subheading", "eyebrow")
    list_filter = ("key", "is_visible")


@admin.register(Service)
class ServiceAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ("preview", "name", "category", "order", "is_active", "show_in_footer")
    list_editable = ("is_active", "show_in_footer")
    sortable_field_name = "order"
    search_fields = ("name", "summary", "description", "category")
    list_filter = ("is_active", "show_in_footer")
    ordering = ("order", "id")
    fieldsets = (
        (None, {"fields": ("name", "category", "summary", "description", "image", "order", "is_active", "show_in_footer")}),
        (
            "Pricing (optional)",
            {"fields": ("price_prefix", "price_amount", "price_suffix")},
        ),
        (
            "Booking",
            {"fields": ("book_button_label", "book_button_url")},
        ),
    )

    @admin.display(description="Image")
    def preview(self, obj):
        return image_preview(obj)


@admin.register(DifferenceItem)
class DifferenceItemAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ("title", "icon", "image_thumb", "text", "order", "is_active")
    list_editable = ("is_active",)
    sortable_field_name = "order"
    search_fields = ("title", "text")
    list_filter = ("is_active",)
    readonly_fields = ("image_thumb",)

    @admin.display(description="Image")
    def image_thumb(self, obj):
        return image_preview(obj, "image")


@admin.register(ProcessStep)
class ProcessStepAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ("title", "number", "text", "order", "is_active")
    list_editable = ("number", "is_active")
    sortable_field_name = "order"
    search_fields = ("title", "text")
    list_filter = ("is_active",)


@admin.register(Testimonial)
class TestimonialAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ("preview", "name", "city", "designation", "rating", "order", "is_active")
    list_editable = ("rating", "is_active")
    sortable_field_name = "order"
    search_fields = ("name", "city", "quote", "designation")
    list_filter = ("is_active", "rating")
    readonly_fields = ("preview",)

    @admin.display(description="Photo")
    def preview(self, obj):
        return image_preview(obj, "photo")


@admin.register(CallToAction)
class CallToActionAdmin(SingletonAdmin):
    fieldsets = (
        ("Visibility", {"fields": ("is_visible",)}),
        ("Banner", {"fields": ("eyebrow", "heading", "text")}),
        (
            "Actions",
            {
                "fields": (
                    "button_label",
                    "button_url",
                    "link_label",
                    "link_url",
                    "secondary_button_label",
                    "secondary_button_url",
                )
            },
        ),
        ("Background", {"fields": ("background_color", "background_image")}),
    )


@admin.register(CtaPoint)
class CtaPointAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ("title", "number", "text", "order", "is_active")
    list_editable = ("number", "is_active")
    sortable_field_name = "order"
    search_fields = ("title", "text")
    list_filter = ("is_active",)


@admin.register(LandingPageSection)
class LandingPageSectionAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ("key", "order", "is_visible", "background_color", "has_bg_image")
    list_editable = ("is_visible",)
    sortable_field_name = "order"
    list_filter = ("is_visible", "key")

    @admin.display(description="BG image", boolean=True)
    def has_bg_image(self, obj):
        return bool(obj.background_image)


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


admin.site.site_header = "Vastra Care — landing page"
admin.site.site_title = "Landing CMS"
admin.site.index_title = "Landing page management"
