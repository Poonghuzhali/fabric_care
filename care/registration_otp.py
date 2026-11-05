import hashlib
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from care.models import CustomerProfile, RegistrationVerification

logger = logging.getLogger(__name__)

OTP_LENGTH = 6
OTP_TTL_MINUTES = 10
MAX_OTP_ATTEMPTS = 5


def _otp_digest(email: str, code: str) -> str:
    payload = f"{email.strip().lower()}:{code}:{settings.SECRET_KEY}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def generate_otp_code() -> str:
    return f"{secrets.randbelow(10**OTP_LENGTH):0{OTP_LENGTH}d}"


def create_or_refresh_verification(*, email, full_name, phone, raw_password):
    email = email.strip().lower()
    code = generate_otp_code()
    expires = timezone.now() + timedelta(minutes=OTP_TTL_MINUTES)
    obj, _created = RegistrationVerification.objects.update_or_create(
        email=email,
        defaults={
            "full_name": full_name,
            "phone": phone,
            "password_hash": make_password(raw_password),
            "otp_hash": _otp_digest(email, code),
            "expires_at": expires,
            "attempts": 0,
        },
    )
    logger.info("Registration OTP refreshed for %s (expires %s)", email, expires.isoformat())
    return code, obj


def resend_otp_for_email(email):
    email = email.strip().lower()
    pending = RegistrationVerification.objects.filter(email=email).first()
    if not pending:
        return None, None, "No pending registration for this email. Please fill the form again."
    code = generate_otp_code()
    pending.otp_hash = _otp_digest(email, code)
    pending.expires_at = timezone.now() + timedelta(minutes=OTP_TTL_MINUTES)
    pending.attempts = 0
    pending.save(update_fields=["otp_hash", "expires_at", "attempts"])
    return code, pending.full_name, ""


def verify_otp_and_create_user(*, email, code):
    email = email.strip().lower()
    pending = RegistrationVerification.objects.filter(email=email).first()
    if not pending:
        return None, "No verification is pending for this email. Please register again."
    if pending.expires_at < timezone.now():
        pending.delete()
        return None, "This OTP has expired. Please request a new code."
    if pending.attempts >= MAX_OTP_ATTEMPTS:
        pending.delete()
        return None, "Too many incorrect attempts. Please register again."
    if _otp_digest(email, code.strip()) != pending.otp_hash:
        pending.attempts += 1
        pending.save(update_fields=["attempts"])
        return None, "Incorrect OTP. Please check the code in your email."
    User = get_user_model()
    if User.objects.filter(email__iexact=email).exists():
        pending.delete()
        return None, "An account with this email already exists. Please sign in."
    user = User(username=email, email=email, is_staff=False)
    user.password = pending.password_hash
    user.save()
    CustomerProfile.objects.create(
        user=user,
        full_name=pending.full_name,
        phone=pending.phone,
    )
    pending.delete()
    return user, ""
