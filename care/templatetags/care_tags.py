from decimal import Decimal

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

ICONS = {
    "loom": '<svg width="__S__" height="__S__" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l7 4v10l-7 4-7-4V7l7-4z"/><path d="M12 21V11"/><path d="M5 7l7 4 7-4"/></svg>',
    "hand": '<svg width="__S__" height="__S__" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 11V6.5a1.5 1.5 0 013 0V11"/><path d="M11 10.5V5.5a1.5 1.5 0 013 0V11"/><path d="M14 11V7.5a1.5 1.5 0 013 0V13c0 3.5-2.2 6-6.2 6H10c-2.4 0-4-1.2-4.8-3L4 13.2a1.4 1.4 0 012.4-1.4L8 13"/></svg>',
    "door": '<svg width="__S__" height="__S__" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 20h16"/><path d="M6 20V5.5A1.5 1.5 0 017.5 4h7A1.5 1.5 0 0116 5.5V20"/><path d="M16 10h3.2a.8.8 0 01.8.8V20"/><circle cx="13.2" cy="12" r=".7" fill="currentColor" stroke="none"/></svg>',
    "spark": '<svg width="__S__" height="__S__" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l1.4 5.2L18.5 9.5 13.4 10.8 12 16l-1.4-5.2L5.5 9.5l5.1-1.3L12 3z"/><path d="M18 14l.6 2 2 .6-2 .6-.6 2-.6-2-2-.6 2-.6.6-2z"/></svg>',
    "shield": '<svg width="__S__" height="__S__" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l7 3v6c0 4.2-2.8 7.2-7 9-4.2-1.8-7-4.8-7-9V6l7-3z"/><path d="M9 12l2 2 4-4"/></svg>',
    "steam": '<svg width="__S__" height="__S__" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><path d="M8 18c-2 0-3-1.4-3-3 0-2 2-3 3.2-1.2"/><path d="M12 18c-2 0-3-1.4-3-3 0-2 2-3 3.2-1.2"/><path d="M16 18c-2 0-3-1.4-3-3 0-2 2-3 3.2-1.2"/></svg>',
    "fold": '<svg width="__S__" height="__S__" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 7h16v3H4z"/><path d="M6 10h12v3H6z"/><path d="M8 13h8v3H8z"/></svg>',
    "clock": '<svg width="__S__" height="__S__" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="8"/><path d="M12 8v4.2L15 14"/></svg>',
    "star": '<svg width="__S__" height="__S__" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 3.6l1.9 4.7 5.1.5-3.9 3.3 1.2 5-4.3-2.6L7.7 17l1.2-5L5 8.8l5.1-.5L12 3.6z"/></svg>',
    "medal": '<svg width="__S__" height="__S__" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="9" r="4"/><path d="M8.5 13.5L7 21l5-2.5L17 21l-1.5-7.5"/></svg>',
    "feather": '<svg width="__S__" height="__S__" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 4s-7 1-11 5-5 11-5 11 7-1 11-5 5-11 5-11z"/><path d="M9 15l-2 2"/></svg>',
    "flower": '<svg width="__S__" height="__S__" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="2"/><path d="M12 4v2M12 18v2M4 12h2M18 12h2M6.3 6.3l1.4 1.4M16.3 16.3l1.4 1.4M17.7 6.3l-1.4 1.4M7.7 16.3l-1.4 1.4"/></svg>',
    "phone": '<svg width="__S__" height="__S__" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><path d="M6.5 4h3l1.5 4-2 1.2a11 11 0 005.8 5.8L18 13l4 1.5v3A2 2 0 0119.8 20 16 16 0 014 6.2 2 2 0 016.5 4z"/></svg>',
    "map": '<svg width="__S__" height="__S__" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><path d="M9 19l-6-3V6l6 3 6-3 6 3v10l-6 3-6-3z"/><path d="M9 6v13M15 3v13"/></svg>',
    "whatsapp": '<svg width="__S__" height="__S__" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 4a8 8 0 00-6.9 12l-.8 3.2 3.3-.8A8 8 0 1012 4zm4.4 11.3c-.2.5-1 .9-1.4 1-.4.1-.8.2-2.7-.6-2.3-.9-3.7-3.2-3.8-3.4-.1-.2-1-1.3-1-2.5s.6-1.8.9-2c.2-.2.5-.3.7-.3h.5c.2 0 .4 0 .5.4.2.5.7 1.7.7 1.8.1.1.1.3 0 .4-.1.2-.2.3-.3.5l-.2.3c-.1.1-.2.2-.1.4.1.2.6 1 1.3 1.6.9.8 1.6 1 1.8 1.1.2.1.3.1.5-.1.2-.2.6-.7.8-.9.2-.2.3-.2.5-.1.2.1 1.4.7 1.6.8.2.1.4.2.4.3.1.2 0 .8-.2 1.3z"/></svg>',
    "clipboard": '<svg width="__S__" height="__S__" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><rect x="7" y="4" width="10" height="4" rx="1"/><path d="M9 8h6v12H9z"/></svg>',
    "wand": '<svg width="__S__" height="__S__" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><path d="M4 20l8-8"/><path d="M13 7l4-4 3 3-4 4"/><path d="M15 5l2 2"/></svg>',
    "check": '<svg width="__S__" height="__S__" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="8"/><path d="M9 12l2 2 4-4"/></svg>',
    "logout": '<svg width="__S__" height="__S__" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/></svg>',
}


@register.simple_tag
def icon(name, size=24):
    svg = ICONS.get(name, ICONS["spark"])
    return mark_safe(svg.replace("__S__", str(int(size))))


@register.simple_tag
def stars(count):
    try:
        filled = max(0, min(5, int(count)))
    except (TypeError, ValueError):
        filled = 0
    parts = []
    star = ICONS["star"].replace("__S__", "14")
    for index in range(5):
        state = "is-on" if index < filled else ""
        parts.append(f'<span class="star {state}">{star}</span>')
    return mark_safe("".join(parts))


def format_inr(value):
    amount = Decimal(value)
    if amount == amount.to_integral():
        return f"₹{int(amount)}"
    return f"₹{amount:.2f}"


@register.filter
def inr(value):
    if value is None or value == "":
        return ""
    return format_inr(value)
