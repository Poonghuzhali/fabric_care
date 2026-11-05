from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from portal import views as portal_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("portal/login/", portal_views.login_view, name="portal_login"),
    path("portal/", include("portal.urls")),
    path("", include("care.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
