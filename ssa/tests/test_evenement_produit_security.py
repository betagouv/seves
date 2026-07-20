from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from playwright.sync_api import Page, expect
import pytest

from core.factories import AgentFactory, ContactAgentFactory, ContactStructureFactory, DocumentFactory
from core.pages import WithContactsPage, WithDocumentsPage
from seves.settings import SSA_GROUP, SV_GROUP
from ssa.factories import EvenementProduitFactory
from ssa.models import EvenementProduit
from ssa.tests.pages import EvenementProduitDetailsPage


def _revoke_ssa_group(user):
    group, _ = Group.objects.get_or_create(name=SSA_GROUP)
    user.groups.remove(group)
    assert not user.groups.filter(name=SSA_GROUP).exists()


def test_soft_delete_missing_ssa_group(live_server, page: Page, mocked_authentification_user):
    evenement = EvenementProduitFactory()
    assert EvenementProduit.objects.count() == 1

    details_page = EvenementProduitDetailsPage(page, live_server.url)
    details_page.navigate(evenement)

    _revoke_ssa_group(mocked_authentification_user)

    details_page.delete()
    expect(page.get_by_text(f"L'évènement {evenement.numero} a bien été supprimé")).not_to_be_visible()
    assert EvenementProduit.objects.count() == 1


def test_publish_missing_ssa_group(live_server, page: Page, mocked_authentification_user):
    evenement = EvenementProduitFactory(etat=EvenementProduit.Etat.BROUILLON, date_publication=None)

    details_page = EvenementProduitDetailsPage(page, live_server.url)
    details_page.navigate(evenement)

    _revoke_ssa_group(mocked_authentification_user)

    details_page.publish()

    evenement.refresh_from_db()
    assert evenement.etat == EvenementProduit.Etat.BROUILLON
    assert evenement.date_publication is None
    expect(page.get_by_text("Événement produit publié avec succès")).not_to_be_visible()


def test_agent_add_missing_ssa_group(live_server, page: Page, mocked_authentification_user, choice_js_fill):
    evenement = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    contact_structure = ContactStructureFactory()
    contact = ContactAgentFactory(
        with_active_agent__with_groups=(SSA_GROUP, SV_GROUP), agent__structure=contact_structure.structure
    )

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    contact_page = WithContactsPage(page)

    _revoke_ssa_group(mocked_authentification_user)

    contact_page.add_agent(choice_js_fill, contact)

    expect(page.get_by_text("L'agent a été ajouté avec succès.")).not_to_be_visible()
    assert EvenementProduit.objects.filter(pk=evenement.pk, contacts=contact).exists() is False


def test_structure_add_missing_ssa_group(live_server, page: Page, mocked_authentification_user, choice_js_fill):
    evenement = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    contact_structure = ContactStructureFactory(with_one_active_agent__with_groups=(SSA_GROUP, SV_GROUP))

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    contact_page = WithContactsPage(page)

    _revoke_ssa_group(mocked_authentification_user)

    contact_page.add_structure(choice_js_fill, contact_structure)

    expect(page.get_by_text("La structure a été ajoutée avec succès.")).not_to_be_visible()
    assert EvenementProduit.objects.filter(pk=evenement.pk, contacts=contact_structure).exists() is False


def test_document_upload_missing_ssa_group(live_server, page: Page, mocked_authentification_user):
    evenement = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    document_page = WithDocumentsPage(page)
    document_page.add_basic_document(close=False)
    document_page.page.wait_for_timeout(5000)
    _revoke_ssa_group(mocked_authentification_user)

    document_page.validate_document_modal(expect_error=True)
    expect(
        page.get_by_text(
            "Les fichiers suivants ont été ajoutés avec succès et seront disponibles après l'analyse antivirus :"
        )
    ).not_to_be_visible()
    evenement.refresh_from_db()
    assert evenement.documents.count() == 0


def test_document_delete_missing_ssa_group(live_server, page: Page, mocked_authentification_user):
    evenement = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    document = DocumentFactory(content_object=evenement)
    evenement.documents.set([document])

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    document_page = WithDocumentsPage(page)

    _revoke_ssa_group(mocked_authentification_user)

    document_page.delete_document(document.pk)

    expect(page.get_by_text("Le document a été marqué comme supprimé.")).not_to_be_visible()
    document.refresh_from_db()
    assert document.is_deleted is False


@pytest.mark.django_db
@pytest.mark.disable_mocked_authentification_user
def test_publish_and_ac_notification_view_ignores_domain_group(client):
    agent = AgentFactory()
    user = agent.user
    user.is_active = True
    user.save()
    assert user.groups.count() == 0
    evenement = EvenementProduitFactory(
        createur=agent.structure, etat=EvenementProduit.Etat.BROUILLON, date_publication=None
    )
    client.force_login(user)

    payload = {
        "content_type_id": ContentType.objects.get_for_model(EvenementProduit).id,
        "content_id": evenement.pk,
    }
    response = client.post(reverse("publish-and-ac-notification"), data=payload)

    assert response.status_code == 403

    evenement.refresh_from_db()
    assert evenement.is_published is False
    assert evenement.etat == EvenementProduit.Etat.BROUILLON
    assert evenement.date_publication is None
