from collections import defaultdict

from django.contrib import messages
from django.contrib.auth import login, logout
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods, require_POST

from care.email_status import email_config_summary
from care.mail import email_delivery_enabled, send_test_email_message
from care.models import Booking, ContactMessage, Service, SiteSetting

from .context import BUCKET_LABELS, booking_bucket, dashboard_stats, portal_context
from .customer_cleanup import delete_customer_by_email, purge_all_bookings, purge_all_customers
from .decorators import portal_login_required
from .forms import BookingStatusForm, PortalLoginForm, ServiceForm, SiteSettingForm, StaffForm
from .models import StaffMember


@ensure_csrf_cookie
def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("portal:dashboard")
        return redirect("account")
    form = PortalLoginForm(request, data=request.POST or None)
    error_note = ""
    if request.GET.get("error") == "access":
        error_note = "This account does not have portal access."
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        if not user.is_staff:
            error_note = "This account does not have portal access."
        else:
            login(request, user, backend="portal.backends.EmailBackend")
            next_url = request.GET.get("next") or request.POST.get("next") or "/portal/"
            return redirect(next_url)
    return render(
        request,
        "portal/login.html",
        {
            "form": form,
            "error_note": error_note,
            "next": request.GET.get("next", ""),
        },
    )


@require_POST
def logout_view(request):
    logout(request)
    return redirect("portal_login")


@portal_login_required
def dashboard(request):
    stats = dashboard_stats()
    ctx = portal_context(request, "Dashboard / Overview", "dashboard")
    ctx.update(stats)
    return render(request, "portal/dashboard.html", ctx)


@portal_login_required
def bookings(request):
    query = (request.GET.get("q") or "").strip()
    bucket = request.GET.get("status", "")
    items = Booking.objects.select_related("service").all()
    if query:
        items = items.filter(
            Q(name__icontains=query)
            | Q(email__icontains=query)
            | Q(phone__icontains=query)
            | Q(service_name__icontains=query)
        )
    if bucket == "pending":
        items = items.filter(status="new")
    elif bucket == "in_progress":
        items = items.filter(status__in=["confirmed", "in_care", "ready"])
    elif bucket == "completed":
        items = items.filter(status="completed")
    ctx = portal_context(request, "Bookings & Service Requests", "bookings", query)
    ctx.update(
        {
            "bookings": items,
            "status_filter": bucket,
            "bucket_labels": BUCKET_LABELS,
            "booking_bucket": booking_bucket,
        }
    )
    return render(request, "portal/bookings.html", ctx)


@portal_login_required
def booking_detail(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    form = BookingStatusForm(request.POST or None, instance=booking)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("portal:bookings")
    ctx = portal_context(request, f"Booking — {booking.name}", "bookings")
    ctx.update({"booking": booking, "form": form, "bucket": booking_bucket(booking.status)})
    return render(request, "portal/booking_detail.html", ctx)


@portal_login_required
@require_POST
def booking_delete(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    label = f"{booking.name} — {booking.service_name}"
    booking.delete()
    messages.success(request, f"Deleted booking for {label}.")
    return redirect("portal:bookings")


@portal_login_required
@require_POST
def bookings_purge_all(request):
    if request.POST.get("confirm") != "DELETE ALL BOOKINGS":
        messages.error(request, "Type DELETE ALL BOOKINGS to confirm clearing every booking.")
        return redirect("portal:bookings")
    count = purge_all_bookings()
    messages.success(request, f"Removed {count} booking record(s).")
    return redirect("portal:bookings")


@portal_login_required
def services(request):
    query = (request.GET.get("q") or "").strip()
    items = Service.objects.all()
    if query:
        items = items.filter(
            Q(name__icontains=query) | Q(summary__icontains=query)
        )
    ctx = portal_context(request, "Manage Services & Pricing", "services", query)
    ctx["services"] = items
    return render(request, "portal/services.html", ctx)


@portal_login_required
@require_http_methods(["GET", "POST"])
def service_create(request):
    form = ServiceForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("portal:services")
    ctx = portal_context(request, "Add service", "services")
    ctx["form"] = form
    return render(request, "portal/service_form.html", ctx)


@portal_login_required
@require_http_methods(["GET", "POST"])
def service_edit(request, pk):
    service = get_object_or_404(Service, pk=pk)
    form = ServiceForm(request.POST or None, request.FILES or None, instance=service)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("portal:services")
    ctx = portal_context(request, f"Edit — {service.name}", "services")
    ctx.update({"form": form, "service": service})
    return render(request, "portal/service_form.html", ctx)


@portal_login_required
@require_POST
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    service.delete()
    return redirect("portal:services")


@portal_login_required
def customers(request):
    query = (request.GET.get("q") or "").strip()
    rows = {}
    for booking in Booking.objects.order_by("-created_at"):
        key = booking.email.lower()
        if key not in rows:
            rows[key] = {
                "name": booking.name,
                "email": booking.email,
                "phone": booking.phone,
                "bookings": 0,
                "last_seen": booking.created_at,
            }
        rows[key]["bookings"] += 1
        if booking.created_at > rows[key]["last_seen"]:
            rows[key]["last_seen"] = booking.created_at
            rows[key]["name"] = booking.name
            rows[key]["phone"] = booking.phone
    for message in ContactMessage.objects.order_by("-created_at"):
        key = message.email.lower()
        if key not in rows:
            rows[key] = {
                "name": message.name,
                "email": message.email,
                "phone": message.phone,
                "bookings": 0,
                "last_seen": message.created_at,
            }
        elif message.created_at > rows[key]["last_seen"]:
            rows[key]["last_seen"] = message.created_at
    customers_list = sorted(rows.values(), key=lambda item: item["last_seen"], reverse=True)
    if query:
        customers_list = [
            row
            for row in customers_list
            if query.lower() in row["email"].lower()
            or query.lower() in row["name"].lower()
            or query in row["phone"]
        ]
    ctx = portal_context(request, "Customers / Users", "customers", query)
    ctx["customers"] = customers_list
    return render(request, "portal/customers.html", ctx)


@portal_login_required
@require_POST
def customer_delete(request):
    email = (request.POST.get("email") or "").strip()
    if not email:
        messages.error(request, "No customer email was provided.")
        return redirect("portal:customers")
    result = delete_customer_by_email(email)
    messages.success(
        request,
        f"Removed {result['bookings']} booking(s), {result['messages']} message(s), "
        f"and {result['users']} login account(s) for {email}.",
    )
    return redirect("portal:customers")


@portal_login_required
@require_POST
def customers_purge_all(request):
    if request.POST.get("confirm") != "DELETE ALL CUSTOMERS":
        messages.error(
            request,
            "Type DELETE ALL CUSTOMERS to confirm removing all bookings, messages, and customer accounts.",
        )
        return redirect("portal:customers")
    result = purge_all_customers()
    messages.success(
        request,
        f"Cleared {result['bookings']} booking(s), {result['messages']} message(s), "
        f"and {result['users']} customer account(s). Staff logins were kept.",
    )
    return redirect("portal:customers")


@portal_login_required
def staff_list(request):
    query = (request.GET.get("q") or "").strip()
    items = StaffMember.objects.all()
    if query:
        items = items.filter(
            Q(full_name__icontains=query)
            | Q(email__icontains=query)
            | Q(phone__icontains=query)
        )
    ctx = portal_context(request, "Staff / Technicians", "staff", query)
    ctx["staff_members"] = items
    return render(request, "portal/staff.html", ctx)


@portal_login_required
@require_http_methods(["GET", "POST"])
def staff_create(request):
    form = StaffForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("portal:staff")
    ctx = portal_context(request, "Add staff member", "staff")
    ctx["form"] = form
    return render(request, "portal/staff_form.html", ctx)


@portal_login_required
@require_http_methods(["GET", "POST"])
def staff_edit(request, pk):
    member = get_object_or_404(StaffMember, pk=pk)
    form = StaffForm(request.POST or None, instance=member)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("portal:staff")
    ctx = portal_context(request, f"Edit — {member.full_name}", "staff")
    ctx.update({"form": form, "member": member})
    return render(request, "portal/staff_form.html", ctx)


@portal_login_required
@require_POST
def staff_delete(request, pk):
    member = get_object_or_404(StaffMember, pk=pk)
    member.delete()
    return redirect("portal:staff")


@portal_login_required
def reports(request):
    stats = dashboard_stats()
    by_service = (
        Booking.objects.values("service_name")
        .annotate(total=Count("id"))
        .order_by("-total")[:8]
    )
    status_breakdown = defaultdict(int)
    for row in Booking.objects.values_list("status", flat=True):
        status_breakdown[booking_bucket(row)] += 1
    ctx = portal_context(request, "Reports & Analytics", "reports")
    status_rows = [(BUCKET_LABELS[key], status_breakdown.get(key, 0)) for key in BUCKET_LABELS]
    ctx.update(
        {
            "stats": stats,
            "by_service": by_service,
            "status_rows": status_rows,
        }
    )
    return render(request, "portal/reports.html", ctx)


@portal_login_required
@require_http_methods(["GET", "POST"])
def settings_view(request):
    site = SiteSetting.objects.first()
    if site is None:
        raise Http404("Site settings are not configured yet.")
    form = SiteSettingForm(request.POST or None, instance=site)
    if request.method == "POST" and request.POST.get("action") == "test_email":
        recipient = (request.POST.get("test_recipient") or request.user.email or "").strip()
        if not recipient:
            messages.error(request, "Enter an email address for the test.")
        elif not email_delivery_enabled():
            messages.error(
                request,
                "Email is not configured on the server. Set BREVO_API_KEY or Brevo SMTP vars in Render Environment.",
            )
        else:
            try:
                send_test_email_message(recipient=recipient, site=site)
                messages.success(request, f"Test email sent to {recipient}. Check inbox and spam.")
            except Exception as exc:
                messages.error(request, f"Test email failed: {exc}")
        return redirect("portal:settings")
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Site settings saved.")
        return redirect("portal:settings")
    ctx = portal_context(request, "Settings", "settings")
    ctx["form"] = form
    ctx["site"] = site
    ctx["email_status"] = email_config_summary()
    return render(request, "portal/settings.html", ctx)
