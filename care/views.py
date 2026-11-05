import json
import logging
from types import SimpleNamespace
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST, require_http_methods

from .decorators import customer_login_required
from .forms import BookingForm, ContactForm, CustomerLoginForm, CustomerRegistrationForm
from .mail import email_delivery_enabled, send_booking_confirmation
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


def _customer_account_redirect(user):
    if user.is_staff:
        return redirect("portal:dashboard")
    return redirect("account")


@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def customer_login(request):
    if request.user.is_authenticated:
        return _customer_account_redirect(request.user)
    form = CustomerLoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        if user.is_staff:
            form.add_error(None, "Staff accounts must use the service portal sign-in.")
        else:
            login(request, user, backend="portal.backends.EmailBackend")
            next_url = request.POST.get("next") or request.GET.get("next") or "/account/"
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
        return redirect("account")
    form = CustomerRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user, backend="portal.backends.EmailBackend")
        messages.success(request, "Your account is ready. You can book a service and track orders here.")
        next_url = request.POST.get("next") or request.GET.get("next") or "/account/"
        return redirect(next_url)
    return render(
        request,
        "account/register.html",
        {
            "form": form,
            "site": SiteSetting.objects.first(),
            "next": request.GET.get("next") or "",
        },
    )


@customer_login_required
def customer_account(request):
    bookings = Booking.objects.filter(customer=request.user).select_related("service")
    profile = request.user.customer_profile
    return render(
        request,
        "account/profile.html",
        {
            "site": SiteSetting.objects.first(),
            "profile": profile,
            "bookings": bookings,
        },
    )


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
    return render(
        request,
        "account/booking_confirmation.html",
        {
            "site": site,
            "booking": booking,
            "email_sent_to": email_sent_to,
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
        "payments_enabled": payments_enabled(),
        "razorpay_key_id": settings.RAZORPAY_KEY_ID if payments_enabled() else "",
        "payments_test_mode": bool(
            payments_enabled() and settings.RAZORPAY_KEY_ID.startswith("rzp_test_")
        ),
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


def _form_response(request, form, success, saved_message, *, booking=None, email_sent_to=""):
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
            payload["redirect"] = reverse("booking_confirmation", kwargs={"booking_id": booking.id})
            payload["email_sent_to"] = email_sent_to or ""
        return JsonResponse(payload)
    if form is not None and form.errors:
        messages.error(request, "Please check the form and try again.")
    elif form is not None:
        messages.success(request, saved_message)
        if booking is not None:
            if email_sent_to:
                request.session[f"booking_{booking.id}_email_sent"] = email_sent_to
            return redirect("booking_confirmation", booking_id=booking.id)
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
        site = SiteSetting.objects.first()
        email_sent_to = ""
        success_message = (
            f"Payment received ({format_inr(service.price)}). Your booking is confirmed."
        )
        if email_delivery_enabled():
            try:
                send_booking_confirmation(booking, site=site)
                email_sent_to = booking.email
                success_message = (
                    f"Payment received ({format_inr(service.price)}). Your booking is confirmed — "
                    f"a confirmation email was sent to {booking.email}."
                )
            except Exception:
                logger.exception("Booking confirmation email failed for booking #%s", booking.pk)
                success_message = (
                    f"Payment received ({format_inr(service.price)}). Your booking is confirmed, "
                    "but we could not send the confirmation email — please check spam or contact the studio."
                )
        else:
            logger.warning(
                "Booking #%s saved; SMTP not configured (EMAIL_HOST_USER/PASSWORD missing on server).",
                booking.pk,
            )
            success_message = (
                f"Payment received ({format_inr(service.price)}). Your booking is confirmed. "
                "(Confirmation email is not set up on the server yet — the studio will contact you.)"
            )
        request.session[f"booking_{booking.id}_email_sent"] = email_sent_to
        return _form_response(
            request,
            form,
            True,
            success_message,
            booking=booking,
            email_sent_to=email_sent_to,
        )
    return _form_response(request, form, False, "")


@require_POST
def contact(request):
    data = _payload(request)
    if data is None:
        return _form_response(request, None, False, "")
    form = ContactForm(data)
    if form.is_valid():
        ContactMessage.objects.create(
            name=form.cleaned_data["name"],
            phone=form.cleaned_data["phone"],
            email=form.cleaned_data["email"],
            message=form.cleaned_data["message"],
        )
        return _form_response(
            request,
            form,
            True,
            "Thank you. Your message has reached the studio.",
        )
    return _form_response(request, form, False, "")
