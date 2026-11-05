from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.customer_login, name="login"),
    path("register/", views.customer_register, name="register"),
    path("account/", views.customer_account, name="account"),
    path("account/orders/<int:booking_id>/", views.customer_order_detail, name="order_detail"),
    path("account/orders/<int:booking_id>/cancel/", views.customer_order_cancel, name="order_cancel"),
    path("account/addresses/add/", views.customer_address_add, name="address_add"),
    path("account/addresses/<int:address_id>/delete/", views.customer_address_delete, name="address_delete"),
    path("account/addresses/<int:address_id>/default/", views.customer_address_default, name="address_default"),
    path("logout/", views.customer_logout, name="customer_logout"),
    path("book/payment-order/", views.book_payment_order, name="book_payment_order"),
    path("book/confirmation/<int:booking_id>/", views.booking_confirmation, name="booking_confirmation"),
    path("book/", views.book, name="book"),
    path("contact/", views.contact, name="contact"),
]
