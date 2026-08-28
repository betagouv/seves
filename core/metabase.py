import time

from django.conf import settings
import jwt


def get_dashboard_token(dashboard_id):
    payload = {"resource": {"dashboard": int(dashboard_id)}, "params": {}, "exp": round(time.time()) + (60 * 10)}
    return jwt.encode(payload, settings.METABASE_SECRET_KEY, algorithm="HS256")
