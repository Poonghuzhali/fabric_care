import re

from django import forms


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
