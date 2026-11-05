from django import forms
from django.contrib.auth.forms import AuthenticationForm

from care.models import Booking, Service, SiteSetting

from .models import StaffMember


class PortalLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username / Email",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "username",
                "placeholder": "admin@serviceportal.com",
                "class": "portal-input",
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={"autocomplete": "current-password", "class": "portal-input"}
        ),
    )


class BookingStatusForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ("status", "notes")
        widgets = {
            "status": forms.Select(attrs={"class": "portal-input"}),
            "notes": forms.Textarea(attrs={"rows": 4, "class": "portal-input"}),
        }


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = (
            "name",
            "summary",
            "description",
            "image",
            "duration",
            "price",
            "order",
            "is_active",
            "show_in_footer",
        )
        labels = {
            "image": "Service photo",
        }
        help_texts = {
            "image": "Shown on the landing page service card. Upload JPEG or PNG to replace the current photo.",
        }
        widgets = {
            "summary": forms.TextInput(attrs={"class": "portal-input"}),
            "description": forms.Textarea(attrs={"rows": 4, "class": "portal-input"}),
            "name": forms.TextInput(attrs={"class": "portal-input"}),
            "duration": forms.TextInput(attrs={"class": "portal-input"}),
            "price": forms.NumberInput(attrs={"class": "portal-input"}),
            "order": forms.NumberInput(attrs={"class": "portal-input"}),
            "image": forms.ClearableFileInput(
                attrs={
                    "class": "portal-file",
                    "accept": "image/jpeg,image/png,image/webp,image/gif",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.image:
            self.fields["image"].required = False


class StaffForm(forms.ModelForm):
    class Meta:
        model = StaffMember
        fields = ("full_name", "email", "phone", "role", "is_active", "notes")
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "portal-input"}),
            "email": forms.EmailInput(attrs={"class": "portal-input"}),
            "phone": forms.TextInput(attrs={"class": "portal-input"}),
            "role": forms.Select(attrs={"class": "portal-input"}),
            "notes": forms.TextInput(attrs={"class": "portal-input"}),
        }


class SiteSettingForm(forms.ModelForm):
    class Meta:
        model = SiteSetting
        fields = (
            "brand_name",
            "tagline",
            "phone",
            "email",
            "address",
            "hours",
            "footer_blurb",
            "copyright_text",
            "slide_seconds",
        )
        widgets = {
            field: forms.TextInput(attrs={"class": "portal-input"})
            for field in (
                "brand_name",
                "tagline",
                "phone",
                "email",
                "address",
                "hours",
                "copyright_text",
            )
        }
        widgets.update(
            {
                "footer_blurb": forms.Textarea(attrs={"rows": 3, "class": "portal-input"}),
                "slide_seconds": forms.NumberInput(attrs={"class": "portal-input"}),
            }
        )
