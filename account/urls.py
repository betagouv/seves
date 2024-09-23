from django.urls import path
from .views import HandlePermissionsView

urlpatterns = [
    path(
        "permissions/",
        HandlePermissionsView.as_view(),
        name="handle-permissions",
    )
]
