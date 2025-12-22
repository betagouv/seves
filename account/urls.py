from django.urls import path
from .views import HandlePermissionsView, HandleAdminsView

urlpatterns = [
    path(
        "permissions/",
        HandlePermissionsView.as_view(),
        name="handle-permissions",
    ),
    path(
        "permissions/admins/",
        HandleAdminsView.as_view(),
        name="handle-admins",
    ),
]
