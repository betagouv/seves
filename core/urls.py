from django.urls import path
from .views import (
    DocumentUploadView
)

urlpatterns = [
    path(
        "document-upload/",
        DocumentUploadView.as_view(),
        name="document-upload",
    ),
]
