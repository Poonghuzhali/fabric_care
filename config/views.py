from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect


def csrf_failure(request, reason=""):
    """
    Browser forms: redirect with a flash message.
    XHR/JSON (e.g. public contact modal): return JSON so the client does not misparse HTML as JSON.
    """
    wants_json = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if wants_json:
        return JsonResponse(
            {
                "ok": False,
                "errors": {
                    "form": (
                        "Your session expired or the page was open too long. "
                        "Refresh the page and try again."
                    ),
                },
            },
            status=403,
        )

    messages.error(
        request,
        "Your session expired or the page was out of date. Refresh the page and try again.",
    )
    return redirect("/")
