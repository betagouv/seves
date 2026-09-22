from functools import wraps

from .models import AuditLog


def get_client_ip(request):
    ip_list = request.META.get("HTTP_X_FORWARDED_FOR")
    if ip_list:
        return ip_list.split(",")[0].strip()


def audit_log(action, method="dispatch"):
    def decorator(cls):
        original = getattr(cls, method)

        @wraps(original)
        def wrapped(self, request, *args, **kwargs):
            AuditLog.objects.create(action=action, user=request.user, path=request.path, ip=get_client_ip(request))
            return original(self, request, *args, **kwargs)

        setattr(cls, method, wrapped)
        return cls

    return decorator
