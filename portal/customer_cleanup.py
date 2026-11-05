from django.contrib.auth import get_user_model

from care.models import Booking, ContactMessage


def delete_customer_by_email(email):
    """Remove bookings, contact messages, and non-staff user account for this email."""
    cleaned = email.strip()
    if not cleaned:
        return {"bookings": 0, "messages": 0, "users": 0}
    bookings, _ = Booking.objects.filter(email__iexact=cleaned).delete()
    messages, _ = ContactMessage.objects.filter(email__iexact=cleaned).delete()
    users, _ = (
        get_user_model()
        .objects.filter(email__iexact=cleaned, is_staff=False)
        .delete()
    )
    return {
        "bookings": bookings,
        "messages": messages,
        "users": users,
    }


def purge_all_bookings():
    count, _ = Booking.objects.all().delete()
    return count


def purge_all_customers():
    booking_count, _ = Booking.objects.all().delete()
    message_count, _ = ContactMessage.objects.all().delete()
    user_count, _ = get_user_model().objects.filter(is_staff=False).delete()
    return {
        "bookings": booking_count,
        "messages": message_count,
        "users": user_count,
    }
