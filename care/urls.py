from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("contact/", views.contact, name="contact"),
    # Legacy URLs — landing site no longer has customer accounts or online booking
    path("login/", RedirectView.as_view(pattern_name="home", permanent=False), name="login"),
    path("register/", RedirectView.as_view(pattern_name="home", permanent=False), name="register"),
    path("account/", RedirectView.as_view(pattern_name="home", permanent=False), name="account"),
    path("logout/", RedirectView.as_view(pattern_name="home", permanent=False), name="customer_logout"),
    path("book/", RedirectView.as_view(pattern_name="home", permanent=False)),
    path("book/payment-order/", RedirectView.as_view(pattern_name="home", permanent=False)),
    path(
        "book/confirmation/<int:booking_id>/",
        RedirectView.as_view(pattern_name="home", permanent=False),
    ),
    path(
        "account/orders/<int:booking_id>/",
        RedirectView.as_view(pattern_name="home", permanent=False),
    ),
    path(
        "account/orders/<int:booking_id>/cancel/",
        RedirectView.as_view(pattern_name="home", permanent=False),
    ),
    path(
        "account/addresses/add/",
        RedirectView.as_view(pattern_name="home", permanent=False),
    ),
    path(
        "account/addresses/<int:address_id>/delete/",
        RedirectView.as_view(pattern_name="home", permanent=False),
    ),
    path(
        "account/addresses/<int:address_id>/default/",
        RedirectView.as_view(pattern_name="home", permanent=False),
    ),
]
