from django.db.models import Sum

from care.models import Booking, ContactMessage, Service

from .navigation import PORTAL_NAV


def booking_bucket(status):
    if status == "new":
        return "pending"
    if status in {"confirmed", "in_care", "ready"}:
        return "in_progress"
    if status == "completed":
        return "completed"
    return "cancelled"


BUCKET_LABELS = {
    "pending": "Pending",
    "in_progress": "In Progress",
    "completed": "Completed",
    "cancelled": "Cancelled",
}


def portal_context(request, page_title, active_slug, search_query=""):
    pending = Booking.objects.filter(status="new").count()
    unread = ContactMessage.objects.filter(is_read=False).count()
    notifications = pending + unread
    return {
        "portal_nav": PORTAL_NAV,
        "portal_page_title": page_title,
        "portal_active": active_slug,
        "portal_search_query": search_query,
        "portal_notifications": notifications,
        "portal_pending_bookings": pending,
        "portal_unread_messages": unread,
        "portal_user": request.user,
    }


def dashboard_stats():
    bookings = Booking.objects.all()
    services = Service.objects.filter(is_active=True)
    revenue = bookings.filter(status="completed").aggregate(
        total=Sum("service__price")
    )["total"]
    return {
        "booking_total": bookings.count(),
        "pending": bookings.filter(status="new").count(),
        "in_progress": bookings.filter(
            status__in=["confirmed", "in_care", "ready"]
        ).count(),
        "completed": bookings.filter(status="completed").count(),
        "active_services": services.count(),
        "revenue": revenue or 0,
        "recent_bookings": bookings.select_related("service")[:6],
    }
