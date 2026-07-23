from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from core.constants import Domains
from core.factories import ContactAgentFactory, ContactStructureFactory, DocumentFactory
from core.models import Document
from seves.settings import SSA_GROUP, SV_GROUP


def _revoke_domain_group(user, object):
    needed_group = Domains.group_for_value(object._meta.app_label)
    group = Group.objects.get(name=needed_group)
    user.groups.remove(group)
    assert not user.groups.filter(name=needed_group).exists()
    return needed_group


def generic_test_cant_upload_document_without_domain_group(client, mocked_authentification_user, object):
    _revoke_domain_group(mocked_authentification_user, object)

    file = SimpleUploadedFile("poc.pdf", b"poc content", content_type="application/pdf")
    response = client.post(
        reverse("document-upload"),
        data={
            "nom": "poc",
            "document_type": Document.TypeDocument.AUTRE,
            "description": "poc",
            "file": file,
            "content_type": ContentType.objects.get_for_model(object).id,
            "object_id": object.pk,
            "next": object.get_absolute_url(),
        },
    )

    object.refresh_from_db()
    assert response.status_code == 403
    assert object.documents.count() == 0


def generic_test_cant_delete_document_without_domain_group(client, mocked_authentification_user, object):
    _revoke_domain_group(mocked_authentification_user, object)

    document = DocumentFactory(content_object=object)
    object.documents.set([document])

    response = client.post(
        reverse("document-delete", kwargs={"pk": document.pk}),
        data={"next": object.get_absolute_url()},
    )

    document.refresh_from_db()
    assert response.status_code == 403, f"Got {response.status_code}"
    assert document.is_deleted is False


def generic_test_cant_add_agent_without_domain_group(client, mocked_authentification_user, object):
    _revoke_domain_group(mocked_authentification_user, object)
    contact = ContactAgentFactory(with_active_agent__with_groups=(SSA_GROUP, SV_GROUP))
    response = client.post(
        reverse("agent-add"),
        data={
            "content_type_id": ContentType.objects.get_for_model(object).id,
            "content_id": object.pk,
            "contacts_agents": contact.pk,
        },
    )

    assert response.status_code == 403
    assert type(object).objects.filter(pk=object.pk, contacts=contact).exists() is False


def generic_test_cant_add_structure_without_domain_group(client, mocked_authentification_user, object):
    _revoke_domain_group(mocked_authentification_user, object)
    contact_structure = ContactStructureFactory(with_one_active_agent__with_groups=(SSA_GROUP, SV_GROUP))
    response = client.post(
        reverse("structure-add"),
        data={
            "content_type_id": ContentType.objects.get_for_model(object).id,
            "content_id": object.pk,
            "contacts_structures": contact_structure.pk,
        },
    )

    assert response.status_code == 403
    assert type(object).objects.filter(pk=object.pk, contacts=contact_structure).exists() is False


def generic_test_cant_publish_without_domain_group(client, mocked_authentification_user, object):
    _revoke_domain_group(mocked_authentification_user, object)
    assert object.is_draft is True

    client.post(
        reverse("publish"),
        data={
            "content_type_id": ContentType.objects.get_for_model(object).id,
            "content_id": object.pk,
            "next": object.get_absolute_url(),
        },
    )

    object.refresh_from_db()
    assert object.is_draft is True


def generic_test_cant_soft_delete_without_domain_group(client, mocked_authentification_user, object):
    _revoke_domain_group(mocked_authentification_user, object)
    assert object.is_deleted is False

    client.post(
        reverse("soft-delete"),
        data={
            "content_type_id": ContentType.objects.get_for_model(object).id,
            "content_id": object.pk,
            "next": object.get_absolute_url(),
        },
    )

    object.refresh_from_db()
    assert object.is_deleted is False


def generic_test_cant_cloturer_without_domain_group(client, mocked_authentification_user, object, ac_structure):
    _revoke_domain_group(mocked_authentification_user, object)
    mocked_authentification_user.agent.structure = ac_structure
    mocked_authentification_user.agent.save()
    assert object.is_cloture is False

    client.post(
        reverse("cloturer", kwargs={"pk": object.pk}),
        data={"content_type_id": ContentType.objects.get_for_model(object).id},
    )

    object.refresh_from_db()
    assert object.is_cloture is False


def generic_test_cant_open_without_domain_group(client, mocked_authentification_user, object, ac_structure):
    _revoke_domain_group(mocked_authentification_user, object)
    mocked_authentification_user.agent.structure = ac_structure
    mocked_authentification_user.agent.save()
    assert object.is_cloture is True

    client.post(
        reverse("evenement-ouvrir", kwargs={"pk": object.pk}),
        data={"content_type_id": ContentType.objects.get_for_model(object).id},
    )

    object.refresh_from_db()
    assert object.is_cloture is True
