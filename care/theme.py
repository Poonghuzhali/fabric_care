"""
Generate inline :root CSS from Site settings (appearance + header/footer).
Falls back to static/css/style.css defaults when fields are blank.
"""

from __future__ import annotations

from html import escape as html_escape_attr
from typing import Any

from django.utils.safestring import mark_safe


def _q(s: str) -> str:
    """Escape for embedding in HTML/CSS text (attributes, style blocks)."""
    return html_escape_attr(s or "", quote=True)

# Defaults mirror static/css/style.css :root
# Brand palette (4 hex colours only — mirrors static/css/style.css)
DEFAULTS = {
    "maroon": "#741F3F",
    "maroon_dark": "#741F3F",  # darker hovers use --ink or opacity in CSS
    "gold": "#CAA55E",
    "cream": "#F9F3E9",
    "ink": "#262221",
    "muted": "rgba(38, 34, 33, 0.62)",  # ink on cream
}


def _font_stack_line_value(stack: str) -> str:
    """
    Value for `font-family: ...` / `:root { --serif: ... }` inside an embedded <style> block.
    Must not add an extra pair of quotes around the whole stack (that breaks var() resolution).
    """
    s = (stack or "").strip().replace("<", "").replace(">", "")
    # Block style injection / broken declarations
    for bad in (";", "}", "/*", "*/", "url(", "@import"):
        if bad in s.lower():
            s = ""
            break
    return s


def section_wrapper_attrs(
    section_row: Any | None,
    *,
    bg_override: str = "",
    text_override: str = "",
    base_classes: str = "",
    extra_style: str = "",
) -> str:
    """Safe HTML attributes for a <section> (extra class + background)."""
    classes: list[str] = [c for c in (base_classes or "").split() if c]
    parts: list[str] = []
    bg = (bg_override or "").strip()
    tx = (text_override or "").strip()
    if section_row is not None:
        ec = (getattr(section_row, "extra_css_class", "") or "").strip()
        if ec:
            classes.extend(ec.split())
        db_bg = (getattr(section_row, "background_color", "") or "").strip()
        if db_bg:
            bg = db_bg
        img = getattr(section_row, "background_image", None)
        if img:
            url = getattr(img, "url", "") or ""
            if url:
                safe_url = _q(url)
                parts.append(f"background-image: url('{safe_url}')")
                parts.append("background-size: cover")
                parts.append("background-position: center")
    if bg:
        parts.insert(0, f"background-color: {_q(bg.strip())}")
    if tx:
        parts.append(f"color: {_q(tx.strip())}")
    es = (extra_style or "").strip().rstrip(";")
    if es:
        parts.append(es)
    attrs: list[str] = []
    if classes:
        attrs.append(f'class="{_q(" ".join(classes))}"')
    if parts:
        attrs.append(f'style="{"; ".join(parts)}"')
    if not attrs:
        return mark_safe("")
    return mark_safe(" ".join(attrs))


def build_theme_css(site: Any) -> str:
    """Return a <style> block safe to embed in base.html (escaped font stacks)."""
    g = DEFAULTS
    p = getattr(site, "color_primary", "") or g["maroon"]
    s = getattr(site, "color_secondary", "") or g["maroon_dark"]
    a = getattr(site, "color_accent", "") or g["gold"]
    cream = getattr(site, "color_page_background", "") or g["cream"]
    ink = getattr(site, "color_body_text", "") or g["ink"]
    head_c = getattr(site, "color_heading_text", "") or g["ink"]
    btn_bg = getattr(site, "button_bg_color", "") or p
    btn_tx = (getattr(site, "button_text_color", "") or "").strip() or g["cream"]
    btn_hov = getattr(site, "button_hover_bg_color", "") or g["ink"]

    # Heading: Cormorant Garamond · body: Mulish (fixed; Site settings do not override)
    serif_stack = _font_stack_line_value('"Cormorant Garamond", serif')
    sans_stack = _font_stack_line_value('"Mulish", sans-serif')
    h_scale = (getattr(site, "heading_size_scale", None) or 100) / 100.0
    b_scale = (getattr(site, "body_size_scale", None) or 100) / 100.0
    radius = getattr(site, "border_radius_px", None)
    if radius is None:
        radius = 18
    spacing = getattr(site, "section_spacing_px", None)
    if spacing is None:
        spacing = 72
    cw = getattr(site, "container_max_width_px", None)
    if cw is None:
        cw = 1160

    logo_h = getattr(site, "logo_max_height_px", None) or 48

    hdr_bg = (getattr(site, "header_bg_color", "") or "").strip()
    hdr_txt = (getattr(site, "header_text_color", "") or "").strip()
    hdr_link = (getattr(site, "header_nav_link_color", "") or "").strip()
    hdr_hover = (getattr(site, "header_nav_link_hover_color", "") or "").strip()
    hdr_cta_bg = (getattr(site, "header_cta_bg", "") or "").strip()
    hdr_cta_tx = (getattr(site, "header_cta_text_color", "") or "").strip()
    hdr_cta_hov = (getattr(site, "header_cta_hover_bg", "") or "").strip()

    # Empty in admin → brochure charcoal (#262221) so production matches static CSS
    ft_bg = (getattr(site, "footer_bg_color", "") or "").strip() or g["ink"]
    ft_tx = (getattr(site, "footer_text_color", "") or "").strip()

    sticky = getattr(site, "header_sticky", True)

    lines: list[str] = [
        ":root {",
        f'  --maroon: {_q(p)};',
        f"  --maroon-dark: {_q(s)};",
        f"  --gold: {_q(a)};",
        f"  --cream: {_q(cream)};",
        f"  --ink: {_q(ink)};",
        f"  --muted: {_q(g['muted'])};",
        f"  --serif: {serif_stack};",
        f"  --sans: {sans_stack};",
        f"  --radius: {int(radius)}px;",
        f"  --heading-scale: {h_scale:.4f};",
        f"  --body-scale: {b_scale:.4f};",
        "}",
        "body {",
        f"  color: {_q(ink)};",
        f"  background: {_q(cream)};",
        f"  font-size: calc(16px * var(--body-scale));",
        "}",
        ".section-title {",
        f"  color: {_q(head_c)};",
        f"  font-size: calc(clamp(36px, 4vw, 52px) * var(--heading-scale));",
        "}",
        ".brand img, .footer-logo {",
        f"  max-height: {int(logo_h)}px;",
        "  width: auto;",
        "}",
        f".band, .about, .cta-wrap {{ padding-block: {int(spacing)}px; }}",
        ".wrap {",
        f"  width: min({int(cw)}px, calc(100% - 48px));",
        "}",
    ]

    if not sticky:
        lines.append(
            ".nav.hero-nav { position: absolute !important; top: 0; left: 0; right: 0; }"
        )

    hero_sel = ".hero-nav .nav-bar"
    if hdr_bg:
        lines.append(f"{hero_sel} {{ background: {_q(hdr_bg)}; }}")
    if hdr_txt:
        lines.append(f"{hero_sel}, .hero-nav .nav-toggle {{ color: {_q(hdr_txt)}; }}")
    if hdr_link:
        lines.append(f".hero-nav .nav-links a {{ color: {_q(hdr_link)}; }}")
    if hdr_hover:
        lines.append(
            f".hero-nav .nav-links a:hover, .hero-nav .nav-links a[aria-current=\"true\"] {{ color: {_q(hdr_hover)}; }}"
        )
    if hdr_cta_bg or hdr_cta_tx or hdr_cta_hov:
        if hdr_cta_bg:
            lines.append(
                f".hero-nav .nav-contact {{ background: {_q(hdr_cta_bg)}; border-color: {_q(hdr_cta_bg)}; }}"
            )
        if hdr_cta_tx:
            lines.append(f".hero-nav .nav-contact {{ color: {_q(hdr_cta_tx)}; }}")
        if hdr_cta_hov:
            lines.append(
                f".hero-nav .nav-contact:hover {{ background: {_q(hdr_cta_hov)}; border-color: {_q(hdr_cta_hov)}; }}"
            )

    if ft_bg:
        lines.append(f".footer {{ background: {_q(ft_bg)}; }}")
    if ft_tx:
        lines.append(f".footer {{ color: {_q(ft_tx)}; }}")
        lines.append(f".footer a {{ color: {_q(ft_tx)}; }}")

    lines.extend(
        [
            ".btn-solid:not(.nav-contact):not(.btn-gold):not(.btn-ghost) {",
            f"  background: {_q(btn_bg)};",
            f"  border-color: {_q(btn_bg)};",
            f"  color: {_q(btn_tx)};",
            "}",
            ".btn-solid:not(.nav-contact):not(.btn-gold):not(.btn-ghost):hover {",
            f"  background: {_q(btn_hov)};",
            f"  border-color: {_q(btn_hov)};",
            "}",
        ]
    )

    return "\n".join(lines) + "\n"
