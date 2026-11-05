from django.utils import timezone

TRACKING_STEPS = (
    ("ordered", "Ordered"),
    ("confirmed", "Confirmed"),
    ("in_progress", "In care"),
    ("completed", "Completed"),
)

CANCELLABLE_STATUSES = frozenset({"new", "confirmed"})


def _step_index(status):
    if status == "new":
        return 0
    if status == "confirmed":
        return 1
    if status in ("in_care", "ready"):
        return 2
    if status == "completed":
        return 3
    return 0


def customer_can_cancel(booking):
    return booking.status in CANCELLABLE_STATUSES and booking.payment_status == "paid"


def order_headline(booking):
    if booking.status == "cancelled":
        return "Order cancelled"
    if booking.status == "completed":
        return "Service completed"
    if booking.status == "ready":
        return "Ready for pickup"
    if booking.status == "in_care":
        return "Your fabrics are in care"
    if booking.status == "confirmed":
        return "Order confirmed"
    preferred = booking.preferred_date
    if preferred and preferred >= timezone.localdate():
        return f"Pickup scheduled for {preferred.strftime('%d %B %Y')}"
    return "Order received"


def tracking_stage_label(booking):
    if booking.status == "cancelled":
        return "Cancelled"
    if booking.status == "ready":
        return "Ready for pickup"
    labels = {
        "new": "Order placed",
        "confirmed": "Confirmed with studio",
        "in_care": "Expert care in progress",
        "completed": "Completed",
    }
    return labels.get(booking.status, "Processing")


def build_tracking_timeline(booking):
    if booking.status == "cancelled":
        return {
            "cancelled": True,
            "steps": [],
            "current_index": -1,
            "progress_percent": 0,
            "stage_label": "This order was cancelled.",
        }
    current = _step_index(booking.status)
    steps = []
    for index, (slug, label) in enumerate(TRACKING_STEPS):
        if slug == "in_progress" and booking.status == "ready":
            label = "Ready"
        steps.append(
            {
                "slug": slug,
                "label": label,
                "done": index < current,
                "active": index == current,
            }
        )
    if booking.status == "completed":
        for step in steps:
            step["done"] = True
            step["active"] = False
        steps[-1]["active"] = True
    progress = 0 if current <= 0 else min(100, int((current / (len(TRACKING_STEPS) - 1)) * 100))
    if booking.status == "completed":
        progress = 100
    return {
        "cancelled": False,
        "steps": steps,
        "current_index": current,
        "progress_percent": progress,
        "stage_label": tracking_stage_label(booking),
    }
