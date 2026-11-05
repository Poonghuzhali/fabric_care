from django.urls import path

from . import views

app_name = "portal"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("bookings/", views.bookings, name="bookings"),
    path("bookings/<int:pk>/", views.booking_detail, name="booking_detail"),
    path("bookings/<int:pk>/delete/", views.booking_delete, name="booking_delete"),
    path("bookings/purge-all/", views.bookings_purge_all, name="bookings_purge_all"),
    path("services/", views.services, name="services"),
    path("services/add/", views.service_create, name="service_create"),
    path("services/<int:pk>/edit/", views.service_edit, name="service_edit"),
    path("services/<int:pk>/delete/", views.service_delete, name="service_delete"),
    path("customers/purge-all/", views.customers_purge_all, name="customers_purge_all"),
    path("customers/delete/", views.customer_delete, name="customer_delete"),
    path("customers/", views.customers, name="customers"),
    path("staff/", views.staff_list, name="staff"),
    path("staff/add/", views.staff_create, name="staff_create"),
    path("staff/<int:pk>/edit/", views.staff_edit, name="staff_edit"),
    path("staff/<int:pk>/delete/", views.staff_delete, name="staff_delete"),
    path("reports/", views.reports, name="reports"),
    path("settings/", views.settings_view, name="settings"),
    path("logout/", views.logout_view, name="logout"),
]
