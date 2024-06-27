from django.urls import path
from .views import (
    DocumentUploadView, DocumentDeleteView
)

urlpatterns = [
    path(
        "document-upload/",
        DocumentUploadView.as_view(),
        name="document-upload",
    ),
    path(
        "document-delete/<int:pk>/",
        DocumentDeleteView.as_view(),
        name="document-delete",
    ),
]
