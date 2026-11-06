import json
import logging

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .forms import ContactForm
from .mail import send_contact_enquiry_notification
from .public_site import (
    is_public_nav_item,
    is_public_nav_url,
    wrap_content_model,
    wrap_hero_slide,
    wrap_nav_link_for_public,
    wrap_section_heading,
    wrap_site_for_public,
)
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

logger = logging.getLogger(__name__)


def _heading(key, eyebrow, heading, subheading=""):
    found = SectionIntro.objects.filter(key=key).first()
    if found and not getattr(found, "is_visible", True):
        from types import SimpleNamespace

        return SimpleNamespace(eyebrow="", heading="", subheading="")
    return wrap_section_heading(found, eyebrow=eyebrow, heading=heading, subheading=subheading)


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


def _form_response(request, form, success, saved_message):
    if _wants_json(request):
        if form is None:
            return JsonResponse({"ok": False, "errors": {"form": "Could not read that request."}}, status=400)
        if form.errors:
            errors = {}
            for key, value in form.errors.items():
                errors[key if key != "__all__" else "form"] = value[0]
            return JsonResponse({"ok": False, "errors": errors}, status=400)
        return JsonResponse({"ok": True, "message": saved_message})
    from django.contrib import messages
    from django.shortcuts import redirect

    if form is not None and form.errors:
        messages.error(request, "Please check the form and try again.")
    elif form is not None:
        messages.success(request, saved_message)
    return redirect("/")


@ensure_csrf_cookie
def home(request):
    site = SiteSetting.objects.first()
    site_public = wrap_site_for_public(site)
    services = [
        wrap_content_model(s) for s in Service.objects.filter(is_active=True).order_by("order", "id")
    ]
    seconds = site.slide_seconds if site else 5
    hero_auto = getattr(site, "hero_auto_advance", True) if site else True

    section_qs = list(LandingPageSection.objects.order_by("order", "id"))
    if not section_qs:
        ordered_sections = [
            {"key": k, "section": None}
            for k in ("about", "services", "difference", "process", "testimonials", "contact")
        ]
    else:
        ordered_sections = []
        for row in section_qs:
            if not getattr(row, "is_visible", True):
                continue
            ordered_sections.append({"key": row.key, "section": row})
    nav_links_all = list(NavLink.objects.filter(is_active=True).order_by("order", "id"))
    nav_links = [
        wrapped
        for link in nav_links_all
        if is_public_nav_item(link.label or "", link.url or "")
        and (wrapped := wrap_nav_link_for_public(link)) is not None
    ]
    footer_links = [
        wrapped
        for link in nav_links_all
        if link.show_in_footer
        and is_public_nav_item(link.label or "", link.url or "")
        and (wrapped := wrap_nav_link_for_public(link)) is not None
    ]
    slides = [
        wrap_hero_slide(s)
        for s in HeroSlide.objects.filter(is_active=True).order_by("order", "id")
    ]
    about_raw = AboutSection.objects.first()
    about = wrap_content_model(about_raw) if about_raw and getattr(about_raw, "is_visible", True) else None

    cta_raw = CallToAction.objects.first()
    cta = wrap_content_model(cta_raw) if cta_raw and getattr(cta_raw, "is_visible", True) else None
    cta_bg_extra = ""
    if cta_raw and getattr(cta_raw, "background_image", None):
        try:
            cta_bg_extra = (
                f"background-image: url('{cta_raw.background_image.url}'); "
                "background-size: cover; background-position: center"
            )
        except Exception:
            cta_bg_extra = ""

    context = {
        "site": site_public,
        "nav_links": nav_links,
        "footer_links": footer_links,
        "slides": slides,
        "hero_auto_advance": hero_auto,
        "ordered_sections": ordered_sections,
        "about": about,
        "features": [wrap_content_model(f) for f in AboutFeature.objects.filter(is_active=True)],
        "services": services,
        "footer_services": [item for item in services if item.show_in_footer],
        "difference_items": [
            wrap_content_model(d) for d in DifferenceItem.objects.filter(is_active=True)
        ],
        "process_steps": [wrap_content_model(p) for p in ProcessStep.objects.filter(is_active=True)],
        "testimonials": [wrap_content_model(t) for t in Testimonial.objects.filter(is_active=True)],
        "cta": cta,
        "cta_background_extra_style": cta_bg_extra,
        "cta_points": [wrap_content_model(c) for c in CtaPoint.objects.filter(is_active=True)],
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
        "ui_copy": {
            "contactFormGenericError": (
                site_public.contact_form_generic_error if site_public else ""
            )
            or "Something went wrong. Please try again.",
            "contactFormNetworkError": (
                site_public.contact_form_network_error if site_public else ""
            )
            or "Something went wrong. Please try again.",
        },
    }
    return render(request, "index.html", context)


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
        success_msg = "Thank you. Your message has reached the studio."
        if site and getattr(site, "contact_success_message", "").strip():
            success_msg = site.contact_success_message.strip()
        return _form_response(
            request,
            form,
            True,
            success_msg,
        )
    return _form_response(request, form, False, "")
