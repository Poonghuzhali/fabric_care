from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect


def customer_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), login_url="/login/")
        if request.user.is_staff:
            return redirect("portal:dashboard")
        if not hasattr(request.user, "customer_profile"):
            return redirect("register")
        return view_func(request, *args, **kwargs)

    return wrapper
