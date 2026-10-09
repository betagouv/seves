from django.conf import settings

from core.constants import Domains


def satisfaction_notice(request):
    if not (settings.ALIM_SATISFACTION_NOTICE_ENABLED and settings.ALIM_SATISFACTION_SURVEY_URL):
        return {}
    if getattr(request, "domain", None) not in (Domains.SSA.value, Domains.TIAC.value):
        return {}
    return {
        "satisfaction_notice": {
            "id": settings.ALIM_SATISFACTION_NOTICE_VERSION,
            "survey_url": settings.ALIM_SATISFACTION_SURVEY_URL,
        }
    }
