from rate_limit.conf import app_settings


def test_settings_can_be_overridden(settings):
    settings.RATELIMIT = {"MAX_REQUESTS_PER_HOUR": 5}

    assert app_settings.MAX_REQUESTS_PER_HOUR == 5
    # Les autres réglages gardent leur valeur par défaut
    assert app_settings.ENABLED is True
