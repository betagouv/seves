from django.urls import path
from . import auth_views
from .views import (
    DocumentUploadView,
    DocumentDeleteView,
    DocumentUpdateView,
    ContactAddFormView,
    ContactSelectionView,
    ContactDeleteView,
    MessageCreateView,
    MessageDetailsView,
    SoftDeleteView,
    StructureAddFormView,
    StructureSelectionView,
    ACNotificationView,
    PublishView,
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
    path(
        "contacts/suppression/",
        ContactDeleteView.as_view(),
        name="contact-delete",
    ),
    path(
        "message-add/<int:obj_type_pk>/<int:obj_pk>/",
        MessageCreateView.as_view(),
        name="message-add",
    ),
    path(
        "message/<int:pk>/",
        MessageDetailsView.as_view(),
        name="message-view",
    ),
    path(
        "suppression/",
        SoftDeleteView.as_view(),
        name="soft-delete",
    ),
    path(
        "publication/",
        PublishView.as_view(),
        name="publish",
    ),
    path(
        "notify-ac/",
        ACNotificationView.as_view(),
        name="notify-ac",
    ),
    path("structures/ajout/selection", StructureAddFormView.as_view(), name="structure-selection-add-form"),
    path("structures/ajout", StructureSelectionView.as_view(), name="structure-add"),
]
