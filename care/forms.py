import re

from decimal import InvalidOperation

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone

from .models import CustomerProfile, Service


class CustomerRegistrationForm(forms.Form):
    full_name = forms.CharField(
        max_length=80,
        label="Full name",
        widget=forms.TextInput(attrs={"autocomplete": "name"}),
    )
    phone = forms.CharField(
        max_length=20,
        label="Phone",
        widget=forms.TextInput(attrs={"autocomplete": "tel"}),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists. Please sign in.")
        return email

    def clean_full_name(self):
        name = " ".join(self.cleaned_data["full_name"].split())
        if len(name) < 2:
            raise forms.ValidationError("Enter your full name.")
        return name

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        digits = re.sub(r"\D", "", phone)
        if len(digits) < 8 or len(digits) > 15:
            raise forms.ValidationError("Enter a valid phone number.")
        return phone

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Passwords do not match.")
        if password1 and "password1" not in self.errors:
            try:
                validate_password(password1)
            except DjangoValidationError as exc:
                self.add_error("password1", " ".join(exc.messages))
        return cleaned

    def save(self):
        User = get_user_model()
        email = self.cleaned_data["email"].lower()
        user = User.objects.create_user(
            username=email,
            email=email,
            password=self.cleaned_data["password1"],
        )
        user.is_staff = False
        user.save(update_fields=["is_staff"])
        CustomerProfile.objects.create(
            user=user,
            full_name=self.cleaned_data["full_name"],
            phone=self.cleaned_data["phone"],
        )
        return user


class CustomerLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Email",
        widget=forms.EmailInput(attrs={"autocomplete": "username", "placeholder": "you@example.com"}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Email or password did not match. Please try again.",
    }


class BookingForm(forms.Form):
    name = forms.CharField(max_length=80)
    phone = forms.CharField(max_length=20)
    email = forms.EmailField()
    service = forms.ModelChoiceField(queryset=Service.objects.none())
    preferred_date = forms.DateField(input_formats=["%Y-%m-%d"])
    pickup_address = forms.CharField(
        max_length=400,
        label="Pickup address",
        widget=forms.TextInput(
            attrs={
                "placeholder": "House / street, area, city, PIN",
                "autocomplete": "street-address",
            }
        ),
    )
    pickup_latitude = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        widget=forms.HiddenInput(),
    )
    pickup_longitude = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        widget=forms.HiddenInput(),
    )
    pickup_maps_url = forms.URLField(required=False, max_length=500)
    notes = forms.CharField(required=False, max_length=800)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        service_field = self.fields["service"]
        service_field.queryset = Service.objects.filter(is_active=True)
        service_field.error_messages["invalid_choice"] = "Please choose a service."
        service_field.required = True
        service_field.empty_label = "Choose a service"
        if user and user.is_authenticated and hasattr(user, "customer_profile"):
            profile = user.customer_profile
            self.fields["name"].initial = profile.full_name
            self.fields["phone"].initial = profile.phone
            self.fields["email"].initial = user.email

    def clean_name(self):
        name = " ".join(self.cleaned_data["name"].split())
        if len(name) < 2:
            raise forms.ValidationError("Enter your full name.")
        return name

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        digits = re.sub(r"\D", "", phone)
        if len(digits) < 8 or len(digits) > 15:
            raise forms.ValidationError("Enter a valid phone number.")
        return phone

    def clean_preferred_date(self):
        chosen = self.cleaned_data["preferred_date"]
        if chosen < timezone.localdate():
            raise forms.ValidationError("Choose today or a later date.")
        return chosen

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if self.user and self.user.is_authenticated and self.user.email.lower() != email:
            raise forms.ValidationError("Use the email on your account.")
        return email

    def clean_pickup_address(self):
        address = " ".join(self.cleaned_data["pickup_address"].split())
        if len(address) < 10:
            raise forms.ValidationError("Enter the full pickup address (at least 10 characters).")
        return address

    def clean(self):
        cleaned = super().clean()
        lat = cleaned.get("pickup_latitude")
        lng = cleaned.get("pickup_longitude")
        if lat is None or lng is None:
            self.add_error(
                "pickup_latitude",
                "Drop a pin on the map for product pickup.",
            )
            return cleaned
        try:
            lat_f = float(lat)
            lng_f = float(lng)
        except (TypeError, ValueError, InvalidOperation):
            self.add_error("pickup_latitude", "Drop a pin on the map for product pickup.")
            return cleaned
        if not (-90 <= lat_f <= 90 and -180 <= lng_f <= 180):
            self.add_error("pickup_latitude", "Invalid map location.")
            return cleaned
        maps_url = (cleaned.get("pickup_maps_url") or "").strip()
        if not maps_url:
            cleaned["pickup_maps_url"] = f"https://www.google.com/maps?q={lat},{lng}"
        return cleaned


class ContactForm(forms.Form):
    name = forms.CharField(max_length=80)
    phone = forms.CharField(max_length=20, required=False)
    email = forms.EmailField()
    message = forms.CharField(max_length=1200)

    def clean_name(self):
        name = " ".join(self.cleaned_data["name"].split())
        if len(name) < 2:
            raise forms.ValidationError("Enter your name.")
        return name

    def clean_phone(self):
        phone = (self.cleaned_data.get("phone") or "").strip()
        if not phone:
            return ""
        digits = re.sub(r"\D", "", phone)
        if len(digits) < 8 or len(digits) > 15:
            raise forms.ValidationError("Enter a valid phone number.")
        return phone

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) < 8:
            raise forms.ValidationError("Please write a short message.")
        return message
