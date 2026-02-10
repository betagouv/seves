"""
URL configuration for seves project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.urls import include, path
from django.views.generic.base import RedirectView
from mozilla_django_oidc.urls import OIDCCallbackClass

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="sv:evenement-liste"), name="index"),
    path("login-eap-callback", OIDCCallbackClass.as_view(), name="custom_oidc_authentication_callback"),
    path("sv/", include("sv.urls", namespace="sv")),
    path("ssa/", include("ssa.urls", namespace="ssa")),
    path("tiac/", include("tiac.urls", namespace="tiac")),
    path("core/", include("core.urls"), name="core"),
    path("account/", include("account.urls"), name="account"),
    path("oidc/", include("mozilla_django_oidc.urls")),
]

if settings.ADMIN_ENABLED:
    from django.contrib import admin

    admin.site.site_header = "Administration de Sèves"
    admin.site.site_title = "Sèves"
    admin.site.index_title = "Bienvenue sur l'administration de Sèves"
    urlpatterns += [
        path(f"{settings.ADMIN_URL}/", admin.site.urls),
    ]

if settings.DEBUG and settings.ENVIRONMENT != "test":
    urlpatterns.append(path("__debug__/", include("debug_toolbar.urls")))
