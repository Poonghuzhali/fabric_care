from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.customer_login, name="login"),
    path("register/", views.customer_register, name="register"),
    path("account/", views.customer_account, name="account"),
    path("logout/", views.customer_logout, name="customer_logout"),
    path("book/payment-order/", views.book_payment_order, name="book_payment_order"),
    path("book/", views.book, name="book"),
    path("contact/", views.contact, name="contact"),
]
