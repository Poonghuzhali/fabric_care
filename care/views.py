import json
import logging
from types import SimpleNamespace
from urllib.parse import quote, urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST, require_http_methods

from .decorators import customer_login_required
from .customer_addresses import remember_customer_address, set_default_address
from .forms import BookingForm, ContactForm, CustomerAddressForm, CustomerLoginForm, CustomerRegistrationForm
from .email_timeout import run_with_timeout
from .mail import (
    email_delivery_enabled,
    send_booking_confirmation,
    send_contact_enquiry_notification,
    send_registration_otp_email,
)
from .registration_otp import (
    OTP_TTL_MINUTES,
    create_or_refresh_verification,
    resend_otp_for_email,
    verify_otp_and_create_user,
)
from .payments import (
    create_service_order,
    payments_enabled,
    price_to_paise,
    verify_payment_signature,
)
from .models import (
    AboutFeature,
    AboutSection,
    Booking,
    CallToAction,
    ContactMessage,
    CustomerAddress,
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
from .order_tracking import build_tracking_timeline, customer_can_cancel
from .templatetags.care_tags import format_inr

logger = logging.getLogger(__name__)


def _heading(key, eyebrow, heading, subheading=""):
    found = SectionIntro.objects.filter(key=key).first()
    if found:
        return found
    return SimpleNamespace(eyebrow=eyebrow, heading=heading, subheading=subheading)


def _payload(request):
    if request.content_type == "application/json":
        try:
            data = json.loads(request.body.decode() or "{}")
        except json.JSONDecodeError:
            return None
        if not isinstance(data, dict):
            return None
        return data
    return request.POST


def _wants_json(request):
    return (
        request.content_type == "application/json"
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
    )


def _booking_login_redirect(request):
    next_path = request.GET.get("next") or "/?open_book=1"
    return redirect(f"/login/?next={quote(next_path, safe='')}")


def _booking_auth_error(request):
    if not request.user.is_authenticated or request.user.is_staff:
        if _wants_json(request):
            return JsonResponse(
                {
                    "ok": False,
                    "errors": {"auth": "Please sign in or register before booking a service."},
                    "redirect": "/login/?next=%2F%3Fopen_book%3D1",
                },
                status=401,
            )
        return _booking_login_redirect(request)
    if not hasattr(request.user, "customer_profile"):
        if _wants_json(request):
            return JsonResponse(
                {
                    "ok": False,
                    "errors": {"auth": "Please complete registration before booking."},
                    "redirect": "/register/?next=%2F%3Fopen_book%3D1",
                },
                status=401,
            )
        return redirect("/register/?next=/?open_book=1")
    return None


def _customer_home_redirect(user):
    if user.is_staff:
        return redirect("portal:dashboard")
    return redirect("home")


@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def customer_login(request):
    if request.user.is_authenticated:
        return _customer_home_redirect(request.user)
    form = CustomerLoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        if user.is_staff:
            form.add_error(None, "Staff accounts must use the service portal sign-in.")
        else:
            login(request, user, backend="portal.backends.EmailBackend")
            next_url = request.POST.get("next") or request.GET.get("next") or "/"
            return redirect(next_url)
    return render(
        request,
        "account/login.html",
        {
            "form": form,
            "site": SiteSetting.objects.first(),
            "next": request.GET.get("next") or request.POST.get("next") or "",
        },
    )


@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def customer_register(request):
    if request.user.is_authenticated and not request.user.is_staff:
        return redirect("home")
    site = SiteSetting.objects.first()
    next_url = request.POST.get("next") or request.GET.get("next") or ""
    otp_sent = request.GET.get("otp_sent") == "1"
    pending_email = (request.GET.get("email") or request.POST.get("email") or "").strip().lower()
    form = CustomerRegistrationForm(request.POST or None)
    action = (request.POST.get("action") or "").strip()

    otp_error = ""

    if request.method == "POST" and action == "verify_otp":
        otp_sent = True
        email = (request.POST.get("email") or "").strip().lower()
        otp = (request.POST.get("otp") or "").strip()
        pending_email = email or pending_email
        if not email:
            otp_error = "Email is required."
        elif len(otp) != 6 or not otp.isdigit():
            otp_error = "Enter the 6-digit code from your email."
        else:
            user, error = verify_otp_and_create_user(email=email, code=otp)
            if error:
                otp_error = error
            else:
                login(request, user, backend="portal.backends.EmailBackend")
                messages.success(request, "Your email is verified. You can book a service from the home page.")
                return redirect(next_url or "/")
    elif request.method == "POST" and action == "resend_otp":
        otp_sent = True
        email = (request.POST.get("email") or "").strip().lower()
        pending_email = email or pending_email
        if not email:
            otp_error = "Email is required."
        elif not email_delivery_enabled():
            otp_error = "Email is not configured yet. Please try again later."
        else:
            code, name, error = resend_otp_for_email(email)
            if error:
                otp_error = error
            else:
                try:
                    run_with_timeout(
                        12,
                        send_registration_otp_email,
                        recipient=email,
                        name=name,
                        otp=code,
                        site=site,
                    )
                except Exception:
                    logger.exception("Registration OTP resend failed for %s", email)
                    otp_error = "We could not resend the OTP email. Please try again shortly."
                else:
                    messages.success(request, f"A new verification code was sent to {email}.")
                    query = f"otp_sent=1&email={quote(email)}"
                    if next_url:
                        query += f"&next={quote(next_url)}"
                    return redirect(f"{reverse('register')}?{query}")
    elif request.method == "POST" and action == "send_otp":
        if form.is_valid():
            if not email_delivery_enabled():
                form.add_error(None, "Email is not configured yet. Please try again later or contact the studio.")
            else:
                code, _pending = create_or_refresh_verification(
                    email=form.cleaned_data["email"],
                    full_name=form.cleaned_data["full_name"],
                    phone=form.cleaned_data["phone"],
                    raw_password=form.cleaned_data["password1"],
                )
                try:
                    run_with_timeout(
                        12,
                        send_registration_otp_email,
                        recipient=form.cleaned_data["email"],
                        name=form.cleaned_data["full_name"],
                        otp=code,
                        site=site,
                    )
                except Exception:
                    logger.exception("Registration OTP email failed for %s", form.cleaned_data["email"])
                    form.add_error(
                        None,
                        "We could not send the OTP email. Check your address or try again in a minute.",
                    )
                else:
                    query = f"otp_sent=1&email={quote(form.cleaned_data['email'])}"
                    if next_url:
                        query += f"&next={quote(next_url)}"
                    messages.success(
                        request,
                        f"We sent a {OTP_TTL_MINUTES}-minute verification code to {form.cleaned_data['email']}.",
                    )
                    return redirect(f"{reverse('register')}?{query}")

    if otp_sent and pending_email and not request.POST:
        form = CustomerRegistrationForm(initial={"email": pending_email})

    return render(
        request,
        "account/register.html",
        {
            "form": form,
            "site": site,
            "next": next_url,
            "otp_sent": otp_sent,
            "pending_email": pending_email,
            "otp_error": otp_error,
        },
    )


@customer_login_required
def customer_account(request):
    bookings = (
        Booking.objects.filter(customer=request.user)
        .select_related("service")
        .order_by("-created_at")
    )
    profile = request.user.customer_profile
    saved_addresses = list(addresses_for_user(request.user))
    address_form = CustomerAddressForm()
    return render(
        request,
        "account/profile.html",
        {
            "site": SiteSetting.objects.first(),
            "profile": profile,
            "bookings": bookings,
            "saved_addresses": saved_addresses,
            "address_form": address_form,
        },
    )


@customer_login_required
def customer_order_detail(request, booking_id):
    booking = get_object_or_404(
        Booking.objects.select_related("service"),
        pk=booking_id,
        customer=request.user,
        payment_status="paid",
    )
    return render(
        request,
        "account/order_detail.html",
        {
            "site": SiteSetting.objects.first(),
            "booking": booking,
            "tracking": build_tracking_timeline(booking),
        },
    )


@customer_login_required
@require_POST
def customer_address_add(request):
    form = CustomerAddressForm(request.POST)
    if not form.is_valid():
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, error)
        return redirect("account")
    remember_customer_address(
        request.user,
        label=form.cleaned_data["label"],
        address=form.cleaned_data["pickup_address"],
        latitude=form.cleaned_data["pickup_latitude"],
        longitude=form.cleaned_data["pickup_longitude"],
        maps_url=form.cleaned_data["pickup_maps_url"],
    )
    messages.success(request, "Address saved to your account.")
    return redirect("account")


@customer_login_required
@require_POST
def customer_address_delete(request, address_id):
    deleted, _ = CustomerAddress.objects.filter(pk=address_id, customer=request.user).delete()
    if deleted:
        messages.success(request, "Address removed.")
    else:
        messages.error(request, "Address not found.")
    return redirect("account")


@customer_login_required
@require_POST
def customer_address_default(request, address_id):
    if set_default_address(request.user, address_id):
        messages.success(request, "Default pickup address updated.")
    else:
        messages.error(request, "Address not found.")
    return redirect("account")


@customer_login_required
@require_POST
def customer_order_cancel(request, booking_id):
    booking = get_object_or_404(
        Booking,
        pk=booking_id,
        customer=request.user,
        payment_status="paid",
    )
    if not customer_can_cancel(booking):
        messages.error(request, "This order can no longer be cancelled online.")
        return redirect("order_detail", booking_id=booking.id)
    booking.status = "cancelled"
    booking.save(update_fields=["status"])
    messages.success(request, f"Order #{booking.id} has been cancelled.")
    return redirect("order_detail", booking_id=booking.id)


@customer_login_required
def booking_confirmation(request, booking_id):
    booking = get_object_or_404(
        Booking.objects.select_related("service"),
        pk=booking_id,
        customer=request.user,
    )
    if booking.payment_status != "paid":
        return redirect("account")
    site = SiteSetting.objects.first()
    email_sent_to = request.session.pop(f"booking_{booking.id}_email_sent", "")
    if not email_sent_to and request.GET.get("emailed") == "1":
        email_sent_to = booking.email
    email_failed = not email_sent_to and request.GET.get("email_failed") == "1"
    return render(
        request,
        "account/booking_confirmation.html",
        {
            "site": site,
            "booking": booking,
            "email_sent_to": email_sent_to,
            "email_failed": email_failed,
            "amount_display": format_inr(booking.amount_paid),
        },
    )


@require_POST
def customer_logout(request):
    logout(request)
    return redirect("home")


def home(request):
    site = SiteSetting.objects.first()
    services = list(Service.objects.filter(is_active=True))
    seconds = site.slide_seconds if site else 5
    payload = []
    for service in services:
        payload.append(
            {
                "id": service.id,
                "name": service.name,
                "summary": service.summary,
                "description": service.description,
                "duration": service.duration,
                "price": format_inr(service.price),
                "price_paise": price_to_paise(service.price),
                "image": service.image.url if service.image else "",
            }
        )
    context = {
        "site": site,
        "nav_links": NavLink.objects.filter(is_active=True),
        "footer_links": NavLink.objects.filter(is_active=True, show_in_footer=True),
        "slides": HeroSlide.objects.filter(is_active=True),
        "about": AboutSection.objects.first(),
        "features": AboutFeature.objects.filter(is_active=True),
        "services": services,
        "footer_services": [item for item in services if item.show_in_footer],
        "services_payload": payload,
        "difference_items": DifferenceItem.objects.filter(is_active=True),
        "process_steps": ProcessStep.objects.filter(is_active=True),
        "testimonials": Testimonial.objects.filter(is_active=True),
        "cta": CallToAction.objects.first(),
        "cta_points": CtaPoint.objects.filter(is_active=True),
        "headings": {
            "services": _heading(
                "services",
                "WHAT WE DO",
                "Our Fabric Care Services",
                "Specialized care and finishing for your everyday wear and traditional fabrics.",
            ),
            "difference": _heading(
                "difference",
                "WHY CHOOSE US",
                "The Vastra Care Difference",
            ),
            "process": _heading(
                "process",
                "HOW IT WORKS",
                "Simple, Careful, Complete",
            ),
            "testimonials": _heading(
                "testimonials",
                "TESTIMONIALS",
                "Loved by Our Customers",
            ),
        },
        "slide_seconds": seconds,
        "google_maps_api_key": getattr(settings, "GOOGLE_MAPS_API_KEY", ""),
    }
    return render(request, "index.html", context)


def _booking_confirmation_path(booking_id, *, email_sent_to="", email_failed=False):
    path = reverse("booking_confirmation", kwargs={"booking_id": booking_id})
    params = {}
    if email_sent_to:
        params["emailed"] = "1"
    elif email_failed:
        params["email_failed"] = "1"
    if params:
        path = f"{path}?{urlencode(params)}"
    return path


def _form_response(request, form, success, saved_message, *, booking=None, email_sent_to="", email_failed=False):
    if _wants_json(request):
        if form is None:
            return JsonResponse({"ok": False, "errors": {"form": "Could not read that request."}}, status=400)
        if form.errors:
            errors = {}
            for key, value in form.errors.items():
                errors[key if key != "__all__" else "form"] = value[0]
            return JsonResponse({"ok": False, "errors": errors}, status=400)
        payload = {"ok": True, "message": saved_message}
        if booking is not None:
            payload["booking_id"] = booking.id
            payload["redirect"] = _booking_confirmation_path(
                booking.id,
                email_sent_to=email_sent_to,
                email_failed=email_failed and not email_sent_to,
            )
            payload["email_sent_to"] = email_sent_to or ""
            payload["order_placed"] = True
        return JsonResponse(payload)
    if form is not None and form.errors:
        messages.error(request, "Please check the form and try again.")
    elif form is not None:
        messages.success(request, saved_message)
        if booking is not None:
            if email_sent_to:
                request.session[f"booking_{booking.id}_email_sent"] = email_sent_to
            return redirect(
                _booking_confirmation_path(
                    booking.id,
                    email_sent_to=email_sent_to,
                    email_failed=email_failed and not email_sent_to,
                )
            )
    return redirect("/")


@require_POST
def book_payment_order(request):
    auth_error = _booking_auth_error(request)
    if auth_error:
        return auth_error
    if not payments_enabled():
        return JsonResponse(
            {
                "ok": False,
                "errors": {
                    "form": "Online payment is not configured yet. Please contact the studio to book."
                },
            },
            status=503,
        )
    data = _payload(request)
    if data is None:
        return JsonResponse({"ok": False, "errors": {"form": "Invalid request."}}, status=400)
    service_id = data.get("service")
    if not service_id:
        return JsonResponse({"ok": False, "errors": {"service": "Please choose a service."}}, status=400)
    service = Service.objects.filter(pk=service_id, is_active=True).first()
    if not service:
        return JsonResponse({"ok": False, "errors": {"service": "Please choose a service."}}, status=400)
    try:
        order, amount_paise = create_service_order(user=request.user, service=service)
    except Exception:
        logger.exception("Could not create Razorpay order for service %s", service_id)
        return JsonResponse(
            {"ok": False, "errors": {"form": "Payment could not be started. Please try again."}},
            status=502,
        )
    site = SiteSetting.objects.first()
    brand = site.brand_name if site and site.brand_name else "Vastra Care"
    return JsonResponse(
        {
            "ok": True,
            "order_id": order["id"],
            "amount": amount_paise,
            "currency": order.get("currency", "INR"),
            "key_id": settings.RAZORPAY_KEY_ID,
            "service_name": service.name,
            "amount_display": format_inr(service.price),
            "brand": brand,
        }
    )


@require_POST
def book(request):
    auth_error = _booking_auth_error(request)
    if auth_error:
        return auth_error
    data = _payload(request)
    if data is None:
        return _form_response(request, None, False, "")
    form = BookingForm(data, user=request.user)
    if form.is_valid():
        service = form.cleaned_data["service"]
        order_id = (data.get("razorpay_order_id") or "").strip()
        payment_id = (data.get("razorpay_payment_id") or "").strip()
        signature = (data.get("razorpay_signature") or "").strip()
        if not payments_enabled() and not getattr(settings, "PAYMENT_SKIP_VERIFY", False):
            return _form_response(
                request,
                form,
                False,
                "",
            ) if not _wants_json(request) else JsonResponse(
                {
                    "ok": False,
                    "errors": {"form": "Online payment is required before booking."},
                },
                status=503,
            )
        if not order_id or not payment_id or not signature:
            if _wants_json(request):
                return JsonResponse(
                    {
                        "ok": False,
                        "errors": {"form": "Please complete payment for this service before submitting."},
                    },
                    status=400,
                )
            messages.error(request, "Please complete payment before booking.")
            return redirect("/?open_book=1")
        if Booking.objects.filter(payment_id=payment_id).exists():
            if _wants_json(request):
                return JsonResponse(
                    {"ok": False, "errors": {"form": "This payment was already used for a booking."}},
                    status=400,
                )
            messages.error(request, "This payment was already used.")
            return redirect("/?open_book=1")
        if not verify_payment_signature(
            order_id=order_id, payment_id=payment_id, signature=signature
        ):
            if _wants_json(request):
                return JsonResponse(
                    {"ok": False, "errors": {"form": "Payment verification failed. Please try again."}},
                    status=400,
                )
            messages.error(request, "Payment verification failed.")
            return redirect("/?open_book=1")
        booking = Booking.objects.create(
            customer=request.user,
            name=form.cleaned_data["name"],
            phone=form.cleaned_data["phone"],
            email=form.cleaned_data["email"],
            service=service,
            service_name=service.name,
            preferred_date=form.cleaned_data["preferred_date"],
            pickup_address=form.cleaned_data["pickup_address"],
            pickup_latitude=form.cleaned_data["pickup_latitude"],
            pickup_longitude=form.cleaned_data["pickup_longitude"],
            pickup_maps_url=form.cleaned_data["pickup_maps_url"],
            notes=form.cleaned_data["notes"],
            amount_paid=service.price,
            payment_order_id=order_id,
            payment_id=payment_id,
            payment_status="paid",
        )
        remember_customer_address(
            request.user,
            address=booking.pickup_address,
            latitude=booking.pickup_latitude,
            longitude=booking.pickup_longitude,
            maps_url=booking.pickup_maps_url,
        )
        site = SiteSetting.objects.first()
        email_sent_to = ""
        email_failed = False
        success_message = f"Your order is placed. Order #{booking.id}."
        if email_delivery_enabled():
            try:
                run_with_timeout(12, send_booking_confirmation, booking, site=site)
                email_sent_to = booking.email
                success_message = (
                    f"Your order is placed. A confirmation email was sent to {booking.email}."
                )
            except Exception:
                email_failed = True
                logger.exception("Booking confirmation email failed for booking #%s", booking.pk)
                success_message = (
                    "Your order is placed, but we could not send the confirmation email. "
                    "The studio will contact you soon."
                )
        else:
            email_failed = True
            logger.warning(
                "Booking #%s saved; SMTP not configured (EMAIL_HOST_USER/PASSWORD missing on server).",
                booking.pk,
            )
            success_message = (
                "Your order is placed. Confirmation email is not configured on the server yet — "
                "the studio will contact you."
            )
        request.session[f"booking_{booking.id}_email_sent"] = email_sent_to
        request.session.modified = True
        return _form_response(
            request,
            form,
            True,
            success_message,
            booking=booking,
            email_sent_to=email_sent_to,
            email_failed=email_failed,
        )
    return _form_response(request, form, False, "")


@require_POST
def contact(request):
    data = _payload(request)
    if data is None:
        return _form_response(request, None, False, "")
    form = ContactForm(data)
    if form.is_valid():
        msg = ContactMessage.objects.create(
            name=form.cleaned_data["name"],
            phone=form.cleaned_data["phone"],
            email=form.cleaned_data["email"],
            message=form.cleaned_data["message"],
        )
        site = SiteSetting.objects.first()
        try:
            send_contact_enquiry_notification(message_obj=msg, site=site)
        except Exception:
            logger.exception("Contact enquiry email failed for message #%s", msg.pk)
        return _form_response(
            request,
            form,
            True,
            "Thank you. Your message has reached the studio.",
        )
    return _form_response(request, form, False, "")
