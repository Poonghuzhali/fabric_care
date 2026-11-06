from .models import SiteSetting
from .theme import build_theme_css


def site_theme(request):
    site = SiteSetting.objects.first()
    if not site:
        return {"theme_css": ""}
    return {"theme_css": build_theme_css(site)}
