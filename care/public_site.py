"""
Sanitize database-driven copy for the public landing page.

Production databases may still contain legacy booking/admin strings from older
versions; we strip those at render time and mirror the same logic in migrations.
"""

from __future__ import annotations

import re
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, Tuple
from urllib.parse import urlparse

if TYPE_CHECKING:
    from .models import HeroSlide, SiteSetting

DEFAULT_COPYRIGHT = "© 2023 Vastra Care. All rights reserved."
DEFAULT_HEADER_CTA = "Book a Service"
DEFAULT_SECONDARY_CTA = "Our Services"

# Matches legacy footer lines and similar
_ADMIN_FOOTER_PAT = re.compile(
    r"django\s*admin|edit\s*site\s*content|/\s*admin\b",
    re.IGNORECASE,
)
# Block nav/footer link labels that advertise admin access.
# Covers Admin, Administrator, Site Admin, SiteAdmin, etc.
# "\b" before "admin" matches inside "badminton" (b|admin|ton); use a negative lookbehind
# on word chars instead. Emails: skip when "admin" is immediately after @ (user@admin.com).
# SiteAdmin: "(?i)admin" after lowercase "e" would not match "Admin" with capital A; a second
# pass removes literal "...Admin..." only when preceded by a lowercase letter (PascalCase tail).
_ADMIN_IN_NAV_CI = re.compile(r"(?<![A-Za-z0-9@])admin\w*", re.IGNORECASE)
_ADMIN_IN_NAV_PASCAL = re.compile(r"(?<=[a-z])Admin\w*")


def _label_advertises_admin(label: str) -> bool:
    raw = (label or "").strip()
    if not raw:
        return False
    return bool(_ADMIN_IN_NAV_CI.search(raw) or _ADMIN_IN_NAV_PASCAL.search(raw))


def is_public_nav_url(url: str) -> bool:
    """False if URL points at Django admin or a #admin hash link."""
    u = (url or "").strip().lower()
    if not u:
        return True
    if u in {"admin", "/admin", "#admin", "/admin/"}:
        return False
    if "/admin" in u or u.startswith("admin/"):
        return False
    if u.startswith("#") and "admin" in u:
        return False
    return True


def sanitize_public_href(url: str | None) -> str:
    """
    Return url for use in public href= attributes, or "" if it must not be linked.

    Blocks Django admin paths, admin hostnames, and javascript: URLs so CMS mistakes
    cannot expose /admin on the brochure site.
    """
    raw = (url or "").strip()
    if not raw:
        return ""
    low = raw.lower()
    if low.startswith("javascript:"):
        return ""
    if not is_public_nav_url(raw):
        return ""
    if low.startswith(("http://", "https://")):
        try:
            parsed = urlparse(raw)
            host = (parsed.netloc or "").lower()
            path = (parsed.path or "").lower()
            if "admin" in host.split(".") or path == "/admin" or path.startswith("/admin/"):
                return ""
        except ValueError:
            return ""
    return raw


def is_public_nav_label(label: str) -> bool:
    """False when the label advertises admin (Admin, Administrator, Site Admin, …)."""
    raw = (label or "").strip()
    if not raw:
        return True
    if _label_advertises_admin(raw):
        return False
    return True


_ADMIN_TOKEN_CI = re.compile(r"(?<![A-Za-z0-9@])admin\w*", re.IGNORECASE)
_ADMIN_TOKEN_PASCAL = re.compile(r"(?<=[a-z])Admin\w*")


def redact_admin_words(text: str) -> str:
    """Remove standalone admin* words from visible copy (keeps emails like user@example.com)."""
    if not (text or "").strip():
        return ""
    out = _ADMIN_TOKEN_PASCAL.sub("", text)
    out = _ADMIN_TOKEN_CI.sub("", out)
    out = re.sub(r"\s{2,}", " ", out)
    # Normalize spacing around , ; : only — do not touch "." (domains like example.com, decimals).
    out = re.sub(r"\s*([,;:])\s*", r"\1 ", out)
    return out.strip(" ,.;:—-–\t\n")


def is_public_nav_item(label: str, url: str) -> bool:
    return is_public_nav_url(url) and is_public_nav_label(label)


def wrap_nav_link_for_public(link) -> SimpleNamespace | None:
    """NavLink row safe for templates: redact camelCase Admin* tails; drop empty labels."""
    if link is None:
        return None
    label = redact_admin_words((link.label or "").strip()).strip()
    if not label:
        return None
    safe_url = sanitize_public_href(getattr(link, "url", "") or "")
    if not safe_url:
        return None
    return SimpleNamespace(
        pk=link.pk,
        label=label,
        url=safe_url,
        show_in_footer=getattr(link, "show_in_footer", False),
    )


def _norm_url(url: str) -> str:
    return (url or "").strip().lower()


def _is_contact_scroll_target(url: str) -> bool:
    u = (url or "").strip()
    ul = u.lower()
    if not u:
        return True
    if ul.startswith("#contact"):
        return True
    if ul.startswith("tel:") or ul.startswith("mailto:"):
        return True
    return False


def _is_services_scroll_target(url: str) -> bool:
    ul = _norm_url(url)
    return ul in {"#services", "#service"} or ul.startswith("#services")


def sanitize_nav_contact_label(text: str) -> str:
    """Header CTA label; empty defaults to Book a Service (scrolls to #contact in template)."""
    t = (text or "").strip()
    return t if t else DEFAULT_HEADER_CTA


def sanitize_footer_blurb(text: str) -> str:
    """Drop legacy lines that advertise Django admin; public footer never shows that."""
    if not (text or "").strip():
        return ""
    kept = []
    for line in (text or "").splitlines():
        low = line.lower()
        if "django admin" in low or "edit site content" in low:
            continue
        if "/admin" in low or ("localhost" in low and "admin" in low):
            continue
        if re.match(r"^\s*admin\s*(—|--|-|–)?\s*edit\s+", low):
            continue
        kept.append(line)
    return "\n".join(kept).strip()


def sanitize_copyright_line(text: str) -> str:
    """Remove Django admin / edit-site hints from copyright; never return those phrases."""
    raw = (text or "").strip()
    if not raw:
        return DEFAULT_COPYRIGHT
    lower = raw.lower()
    if "django admin" in lower or "edit site content" in lower or "/admin" in lower:
        # Drop an em-dash or hyphen segment that starts the admin hint
        cleaned = re.split(r"\s*[—\-–]\s*", raw, maxsplit=1)[0].strip()
        if _ADMIN_FOOTER_PAT.search(cleaned):
            cleaned = _ADMIN_FOOTER_PAT.sub("", cleaned)
        cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" —-–")
        if not cleaned or len(cleaned) < 6:
            return DEFAULT_COPYRIGHT
        return cleaned[:180]
    return raw[:180]


def sanitize_hero_cta(
    primary_label: str, primary_url: str, secondary_label: str, secondary_url: str
) -> Tuple[str, str, str, str]:
    """Keep brochure-style Book CTAs; strip admin links and map legacy copy to #contact / #services."""
    pl = (primary_label or "").strip()
    pu = (primary_url or "").strip()
    sl = (secondary_label or "").strip()
    su = (secondary_url or "").strip()

    if not is_public_nav_url(pu):
        pu = "#contact"
    if su and not is_public_nav_url(su):
        su = "#services"

    if re.search(r"\bbook\b", pl, re.IGNORECASE):
        if not _is_contact_scroll_target(pu):
            pl = "Book Now"
            pu = "#contact"
        elif not pu:
            pu = "#contact"
    elif re.search(r"\bcontact us\b", pl, re.IGNORECASE) and _is_contact_scroll_target(pu):
        pl = "Book Now"
        pu = pu or "#contact"

    if re.search(r"\bbook\b", sl, re.IGNORECASE):
        if not _is_services_scroll_target(su):
            sl = DEFAULT_SECONDARY_CTA
            su = "#services"
        elif not su:
            su = "#services"

    return (
        pl or "Book Now",
        pu or "#contact",
        sl or DEFAULT_SECONDARY_CTA,
        su or "#services",
    )


def wrap_site_for_public(site: SiteSetting | None) -> Any:
    """Copy site row with nav/copyright strings safe for the public page."""
    if site is None:
        return None
    skip_redact = {"email", "enquiry_inbox_email"}
    data = {}
    for f in site._meta.fields:
        name = f.name
        val = getattr(site, name)
        if name.endswith("_url") or name == "nav_contact_url":
            if isinstance(val, str):
                data[name] = sanitize_public_href(val)
            else:
                data[name] = val
        elif name in skip_redact:
            data[name] = val
        elif isinstance(val, str):
            max_len = getattr(f, "max_length", None)
            cleaned = redact_admin_words(val)
            if max_len:
                cleaned = cleaned[:max_len]
            data[name] = cleaned
        else:
            data[name] = val
    data["nav_contact_label"] = sanitize_nav_contact_label(data.get("nav_contact_label", ""))
    data["copyright_text"] = sanitize_copyright_line(site.copyright_text)
    data["footer_blurb"] = sanitize_footer_blurb(data.get("footer_blurb", "") or "")
    return SimpleNamespace(**data)


def wrap_content_model(instance):
    """Shallow public view of any content model: strip admin* tokens from strings."""
    if instance is None:
        return None
    data = {}
    for f in instance._meta.fields:
        name = f.name
        val = getattr(instance, name)
        if isinstance(val, str):
            if name.endswith("_url"):
                data[name] = sanitize_public_href(val)
            else:
                max_len = getattr(f, "max_length", None)
                cleaned = redact_admin_words(val)
                if max_len:
                    cleaned = cleaned[:max_len]
                data[name] = cleaned
        else:
            data[name] = val
    if hasattr(instance, "initial"):
        try:
            ini = instance.initial
            if isinstance(ini, str):
                data["initial"] = redact_admin_words(ini)[:1] or "I"
            else:
                data["initial"] = ini
        except Exception:
            pass
    return SimpleNamespace(**data)


def wrap_section_heading(obj, *, eyebrow: str, heading: str, subheading: str = ""):
    """Public section intro from DB row or fallback SimpleNamespace."""
    from types import SimpleNamespace as SN

    if obj is None:
        return SN(
            eyebrow=redact_admin_words(eyebrow),
            heading=redact_admin_words(heading),
            subheading=redact_admin_words(subheading),
        )
    wrapped = wrap_content_model(obj)
    return SN(
        eyebrow=wrapped.eyebrow,
        heading=wrapped.heading,
        subheading=getattr(wrapped, "subheading", "") or "",
    )


def wrap_hero_slide(slide: HeroSlide) -> Any:
    """Copy hero slide with booking-style CTAs replaced for public display."""
    base = wrap_content_model(slide)
    data = vars(base).copy()
    pl, pu, sl, su = sanitize_hero_cta(
        data.get("primary_label") or "",
        data.get("primary_url") or "",
        data.get("secondary_label") or "",
        data.get("secondary_url") or "",
    )
    pl = redact_admin_words(pl)
    sl = redact_admin_words(sl)
    data.update(
        primary_label=pl or "Book Now",
        primary_url=sanitize_public_href(pu) or "#contact",
        secondary_label=sl or DEFAULT_SECONDARY_CTA,
        secondary_url=sanitize_public_href(su) or "#services",
    )
    return SimpleNamespace(**data)
