import re

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve as serve_media

from portal import views as portal_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("portal/login/", portal_views.login_view, name="portal_login"),
    path("portal/", include("portal.urls")),
    path("", include("care.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Render / demo: serve seeded uploads from disk (use object storage at scale).
    media_url = settings.MEDIA_URL.lstrip("/")
    if media_url and not media_url.endswith("/"):
        media_url += "/"
    urlpatterns += [
        re_path(
            r"^" + re.escape(media_url) + r"(?P<path>.*)$",
            serve_media,
            {"document_root": settings.MEDIA_ROOT, "show_indexes": False},
        ),
    ]
