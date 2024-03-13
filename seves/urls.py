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
from django.contrib import admin
from django.urls import path, include

# Personnalisation du titre et de l'en-tête de l'interface d'administration
admin.site.site_header = "Administration de Sèves"
admin.site.site_title = "Sèves"
admin.site.index_title = "Bienvenue sur l'administration de Sèves"

urlpatterns = [
    path('admin/', admin.site.urls),
	path("sv/", include("sv.urls"), name="sv-index"),
]
