from django.http import HttpResponseForbidden, JsonResponse
from functools import wraps

def role_required(role):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.role != role:
                if request.headers.get("Content-Type") == "application/json" or request.path.startswith("/pwa/api/"):
                    return JsonResponse({"status": "error", "message": "Access denied"}, status=403)
                return HttpResponseForbidden("Access denied")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator