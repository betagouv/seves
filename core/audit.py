from functools import wraps

from .models import AuditLog


def audit_log(action, method="dispatch"):
    def decorator(cls):
        original = getattr(cls, method)

        @wraps(original)
        def wrapped(self, request, *args, **kwargs):
            AuditLog.objects.create(
                action=action,
                user=request.user,
                path=request.path,
            )
            return original(self, request, *args, **kwargs)

        setattr(cls, method, wrapped)
        return cls

    return decorator
