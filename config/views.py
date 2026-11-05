from django.contrib import messages
from django.shortcuts import redirect


def csrf_failure(request, reason=""):
    """Send users back to sign-in instead of a bare 403 (common on mobile stale forms)."""
    login_path = request.path if request.path.endswith("/login/") else "/login/"
    if request.path.startswith("/portal"):
        login_path = "/portal/login/"
    messages.error(
        request,
        "Your session expired or the form was out of date. Please sign in again.",
    )
    return redirect(login_path)
