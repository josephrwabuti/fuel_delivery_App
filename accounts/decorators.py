from django.http import HttpResponseForbidden
from functools import wraps

def role_required(role):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.role != role:
                return HttpResponseForbidden("Access denied")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator