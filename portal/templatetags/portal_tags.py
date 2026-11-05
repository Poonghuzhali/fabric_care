from django import template

from portal.context import BUCKET_LABELS, booking_bucket

register = template.Library()


@register.filter
def portal_bucket(status):
    return booking_bucket(status)


@register.filter
def portal_bucket_label(status):
    return BUCKET_LABELS.get(booking_bucket(status), status)


@register.simple_tag
def portal_badge_class(status):
    bucket = booking_bucket(status)
    return f"badge badge--{bucket.replace('_', '-')}"
