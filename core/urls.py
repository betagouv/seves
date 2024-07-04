from django.urls import path
from .views import DocumentUploadView, DocumentDeleteView, DocumentUpdateView

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
    path(
        "document-update/<int:pk>/",
        DocumentUpdateView.as_view(),
        name="document-update",
    ),
]
