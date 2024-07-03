from django.urls import path
from . import auth_views
from .views import DocumentUploadView, DocumentDeleteView, DocumentUpdateView, ContactAddFormView, ContactSelectionView

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
    path(
        "login",
        auth_views.LoginView.as_view(),
        name="login",
    ),
    path(
        "logout",
        auth_views.logout,
        name="logout",
    ),
    path("contacts/ajout", ContactAddFormView.as_view(), name="contact-add-form"),
    path("contacts/ajout/agents", ContactSelectionView.as_view(), name="contact-add-form-select-agents"),
]
