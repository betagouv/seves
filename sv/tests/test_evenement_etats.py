import html

import pytest
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from playwright.sync_api import Page, expect

from core.constants import AC_STRUCTURE, MUS_STRUCTURE, BSV_STRUCTURE
from core.factories import ContactStructureFactory, StructureFactory
from core.models import Contact, FinSuiviContact, Visibilite
from sv.factories import EvenementFactory
from sv.models import Structure, Evenement


@pytest.fixture
def contact_ac(db):
    ac_structure = Structure.objects.create(niveau1=AC_STRUCTURE, niveau2=MUS_STRUCTURE, libelle=MUS_STRUCTURE)
    return Contact.objects.create(structure=ac_structure)


def _add_contacts(evenement, mocked_authentification_user):
    """Ajoute l'agent et la structure de l'agent connecté aux contacts."""
    user_contact_agent = Contact.objects.get(agent=mocked_authentification_user.agent)
    user_contact_structure = Contact.objects.get(structure=mocked_authentification_user.agent.structure)
    evenement.contacts.add(user_contact_agent)
    evenement.contacts.add(user_contact_structure)


def test_can_cloturer_evenement_if_creator_structure_in_fin_suivi(
    live_server, page: Page, mocked_authentification_user, contact_ac: Contact
):
    """Test qu'un agent de l'AC connecté peut cloturer un événement si la structure du créateur (seule présente dans la liste des contacts) de la événement est en fin de suivi."""
    evenement = EvenementFactory()
    contact_structure = ContactStructureFactory()
    evenement.contacts.add(contact_structure)
    FinSuiviContact(
        content_type=ContentType.objects.get_for_model(evenement), object_id=evenement.id, contact=contact_structure
    ).save()
    mocked_authentification_user.agent.structure = contact_ac.structure

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    page.get_by_role("link", name="Clôturer l'événement").click()
    page.get_by_role("button", name="Clôturer").click()

    expect(page.get_by_text(f"L'événement n°{evenement.numero} a bien été clôturé.")).to_be_visible()
    expect(page.get_by_text("Clôturé", exact=True)).to_be_visible()
    evenement.refresh_from_db()
    assert evenement.etat == Evenement.Etat.CLOTURE


def test_can_cloturer_evenement_if_contacts_structures_in_fin_suivi(
    live_server, page: Page, mocked_authentification_user, contact_ac: Contact
):
    """Test qu'un agent de l'AC connecté peut cloturer un événement si toutes les structures de la liste des contacts sont en fin de suivi."""
    evenement = EvenementFactory()
    mocked_authentification_user.agent.structure = contact_ac.structure
    contact2 = ContactStructureFactory()

    evenement.contacts.add(contact2)
    evenement.contacts.add(contact_ac)

    content_type = ContentType.objects.get_for_model(evenement)
    FinSuiviContact.objects.create(content_type=content_type, object_id=evenement.id, contact=contact2)
    FinSuiviContact.objects.create(
        content_type=content_type,
        object_id=evenement.id,
        contact=contact_ac,
    )

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    page.get_by_role("link", name="Clôturer l'événement").click()
    page.get_by_role("button", name="Clôturer").click()

    evenement.refresh_from_db()
    assert evenement.etat == Evenement.Etat.CLOTURE


def test_can_cloturer_evenement_if_creator_structure_not_in_fin_suivi(
    live_server, page: Page, mocked_authentification_user, contact_ac: Contact
):
    """Test qu'un agent de l'AC connecté peut cloturer un evenement si la structure du créateur de l'événement n'est pas en fin de suivi."""
    evenement = EvenementFactory()
    mocked_authentification_user.agent.structure = contact_ac.structure
    evenement.contacts.add(contact_ac)
    evenement.contacts.add(ContactStructureFactory(structure=evenement.createur))

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    page.get_by_role("link", name="Clôturer l'événement").click()

    expect(
        page.get_by_label("Clôturer l'événement").get_by_text(
            "Pour information, les structures suivantes n’ont pas signalé la fin de suivi :"
        )
    ).to_be_visible()
    expect(page.get_by_label("Clôturer l'événement").get_by_text(contact_ac.structure.libelle)).to_be_visible()
    expect(
        page.get_by_label("Clôturer l'événement").get_by_text(
            f"Souhaitez-vous tout de même procéder à la clôture de l'événement {evenement.numero} ?"
        )
    ).to_be_visible()
    evenement.refresh_from_db()
    assert evenement.etat == Evenement.Etat.EN_COURS


def test_can_cloturer_evenement_if_on_off_contacts_structures_not_in_fin_suivi(
    live_server, page: Page, mocked_authentification_user, contact_ac: Contact
):
    """Test qu'un agent de l'AC connecté peut cloturer un événement si une structure de la liste des contacts n'est pas en fin de suivi."""
    evenement = EvenementFactory()
    mocked_authentification_user.agent.structure = contact_ac.structure
    contact2 = ContactStructureFactory()
    evenement.contacts.add(contact2)
    evenement.contacts.add(contact_ac)
    FinSuiviContact.objects.create(
        content_type=ContentType.objects.get_for_model(evenement),
        object_id=evenement.id,
        contact=contact_ac,
    )

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    page.get_by_role("link", name="Clôturer l'événement").click()

    expect(
        page.get_by_label("Clôturer l'événement").get_by_text(
            "Pour information, les structures suivantes n’ont pas signalé la fin de suivi :"
        )
    ).to_be_visible()
    expect(page.get_by_label("Clôturer l'événement").get_by_text(contact2.structure.libelle)).to_be_visible()
    expect(
        page.get_by_label("Clôturer l'événement").get_by_text(
            f"Souhaitez-vous tout de même procéder à la clôture de l'événement {evenement.numero} ?"
        )
    ).to_be_visible()
    page.get_by_role("button", name="Clôturer").click()

    evenement.refresh_from_db()
    assert evenement.etat == Evenement.Etat.CLOTURE


def test_cannot_cloturer_evenement_if_user_is_not_ac(live_server, page: Page, mocked_authentification_user):
    """Test qu'un agent connecté non membre de l'AC ne peut pas cloturer un événement même si la/les structure(s) de la liste des contacts sont en fin de suivi."""
    evenement = EvenementFactory()
    contact = ContactStructureFactory()
    evenement.contacts.add(contact)
    FinSuiviContact.objects.create(
        content_type=ContentType.objects.get_for_model(evenement), object_id=evenement.id, contact=contact
    )

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()

    expect(page.get_by_role("link", name="Clôturer l'événement")).not_to_be_visible()
    evenement.refresh_from_db()
    assert evenement.etat == Evenement.Etat.EN_COURS


def test_cloture_evenement_auto_fin_suivi_si_derniere_structure_ac(
    live_server, page: Page, mocked_authentification_user
):
    """Test qu'une structure de l'AC peut clôturer un événement si elle est la dernière structure de la liste des contacts à ne pas avoir signalé la fin de suivi.
    Dans ce cas, l'état 'fin de suivi' est ajouté à la structure de l'AC et un message fin de suivi est ajouté automatiquement."""
    evenement = EvenementFactory()
    contact_mus = ContactStructureFactory(
        structure__niveau1=AC_STRUCTURE, structure__niveau2=MUS_STRUCTURE, structure__libelle=MUS_STRUCTURE
    )
    contact_1 = ContactStructureFactory()
    evenement.contacts.set([contact_mus, contact_1])
    evenement_content_type = ContentType.objects.get_for_model(evenement)
    FinSuiviContact(content_type=evenement_content_type, object_id=evenement.id, contact=contact_1).save()
    mocked_authentification_user.agent.structure = contact_mus.structure
    mocked_authentification_user.agent.save()

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    page.get_by_role("link", name="Clôturer l'événement").click()
    expect(page.get_by_text(f"Confirmez-vous la clôture de l’événement {evenement.numero}")).to_be_visible()
    page.get_by_role("button", name="Clôturer").click()

    expect(page.get_by_text(f"L'événement n°{evenement.numero} a bien été clôturé.")).to_be_visible()
    evenement.refresh_from_db()
    assert evenement.etat == Evenement.Etat.CLOTURE
    assert FinSuiviContact.objects.filter(
        content_type=evenement_content_type, object_id=evenement.id, contact=contact_mus
    ).exists()


def test_show_cloture_tag(live_server, page: Page):
    evenement = EvenementFactory(etat=Evenement.Etat.CLOTURE)
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    expect(page.get_by_text("Clôturé")).to_be_visible()


@pytest.mark.django_db
def test_cant_publish_evenement_i_cant_see(client):
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON, createur=StructureFactory())
    response = client.get(evenement.get_absolute_url())
    assert response.status_code == 403

    response = client.post(
        reverse("publish"),
        data={
            "content_type_id": ContentType.objects.get_for_model(evenement).id,
            "content_id": evenement.id,
        },
    )

    assert response.status_code == 302
    assert evenement.etat == Evenement.Etat.BROUILLON


def test_cant_see_cloture_evenement_button_if_is_already_cloture(live_server, page: Page):
    evenement = EvenementFactory(etat=Evenement.Etat.CLOTURE)
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    expect(page.get_by_role("button", name="Actions")).not_to_be_visible()
    expect(page.get_by_role("link", name="Clôturer l'événement")).not_to_be_visible()


def test_cant_cloture_evenement_if_already_cloture(client):
    evenement = EvenementFactory(etat=Evenement.Etat.CLOTURE)

    response = client.post(
        reverse("cloturer", kwargs={"pk": evenement.id}),
        data={"content_type_id": ContentType.objects.get_for_model(evenement).id},
    )

    evenement.refresh_from_db()
    assert response.status_code == 302
    assert evenement.is_deleted is False


@pytest.mark.django_db
def test_can_ouvrir_evenement_if_cloture(live_server, page: Page, mocked_authentification_user, contact_ac):
    evenement = EvenementFactory(etat=Evenement.Etat.CLOTURE)
    mocked_authentification_user.agent.structure = contact_ac.structure
    FinSuiviContact.objects.create(
        content_type=ContentType.objects.get_for_model(Evenement), object_id=evenement.id, contact=contact_ac
    )

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("button", name="Ouvrir l'évènement").click()
    page.get_by_role("button", name="Confirmer", exact=True).click()

    expect(page.get_by_text(f"L'événement {evenement.numero} a bien été ouvert de nouveau.")).to_be_visible()
    evenement.refresh_from_db()
    assert evenement.etat == Evenement.Etat.EN_COURS
    assert not evenement.fin_suivi.filter(contact=contact_ac).exists()


@pytest.mark.django_db
def test_cant_ouvrir_evenement_if_draft(live_server, page: Page, client):
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    expect(page.get_by_role("button", name="Ouvrir l'évènement")).not_to_be_visible()

    response = client.post(
        reverse("evenement-ouvrir", kwargs={"pk": evenement.id}),
        data={"content_type_id": ContentType.objects.get_for_model(evenement).id},
        follow=True,
    )
    assert response.status_code == 200
    evenement.refresh_from_db()
    assert evenement.etat == Evenement.Etat.BROUILLON
    assert "Vous ne pouvez pas ouvrir l'évènement." in html.unescape(response.content.decode())


@pytest.mark.django_db
def test_cant_ouvrir_evenement_if_en_cours(live_server, page: Page, client, mocked_authentification_user, contact_ac):
    evenement = EvenementFactory(etat=Evenement.Etat.EN_COURS)
    mocked_authentification_user.agent.structure = contact_ac.structure

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    expect(page.get_by_role("button", name="Ouvrir l'évènement")).not_to_be_visible()

    response = client.post(
        reverse("evenement-ouvrir", kwargs={"pk": evenement.id}),
        data={"content_type_id": ContentType.objects.get_for_model(evenement).id},
        follow=True,
    )
    assert response.status_code == 200
    evenement.refresh_from_db()
    assert evenement.etat == Evenement.Etat.EN_COURS
    assert "Vous ne pouvez pas ouvrir l'évènement." in html.unescape(response.content.decode())


@pytest.mark.django_db
def test_cant_ouvrir_evenement_if_user_is_not_ac(live_server, page: Page, client):
    evenement = EvenementFactory(etat=Evenement.Etat.CLOTURE, visibilite=Visibilite.NATIONALE)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    expect(page.get_by_role("button", name="Ouvrir l'évènement")).not_to_be_visible()

    response = client.post(
        reverse("evenement-ouvrir", kwargs={"pk": evenement.id}),
        data={"content_type_id": ContentType.objects.get_for_model(evenement).id},
        follow=True,
    )
    assert response.status_code == 200
    evenement.refresh_from_db()
    assert evenement.etat == Evenement.Etat.CLOTURE
    assert "Vous ne pouvez pas ouvrir l'évènement." in html.unescape(response.content.decode())


@pytest.mark.django_db
def test_can_publish_evenement(live_server, page: Page):
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    publish_btn = page.get_by_role("button", name="Publier sans déclarer à l'AC")
    expect(publish_btn).to_be_enabled()
    publish_btn.click()
    page.get_by_text("Publier l'événement").click()

    expect(page.get_by_text(f"Événement {evenement.numero} publié avec succès")).to_be_visible()
    expect(publish_btn).not_to_be_visible()
    evenement.refresh_from_db()
    assert evenement.is_published is True


@pytest.mark.django_db
def test_cant_forge_publication_of_evenement_we_are_not_owner(client, mocked_authentification_user):
    evenement = EvenementFactory(
        createur=Structure.objects.create(libelle="A new structure"), etat=Evenement.Etat.BROUILLON
    )
    response = client.get(evenement.get_absolute_url())

    assert response.status_code == 403

    payload = {
        "content_type_id": ContentType.objects.get_for_model(evenement).id,
        "content_id": evenement.pk,
    }
    response = client.post(reverse("publish"), data=payload)

    assert response.status_code == 302
    evenement.refresh_from_db()
    assert evenement.is_draft is True


def test_publish_without_notifier_ac_show_modal(live_server, page: Page):
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("button", name="Publier sans déclarer à l'AC").click()

    expect(page.get_by_role("heading", name="Publier sans déclarer à l'AC")).to_be_visible()
    expect(
        page.get_by_text(
            "L'administration centrale ne sera pas notifiée de la publication de cet événement. Vous pourrez le faire plus tard avec le bouton \"Déclarer à l'AC\" dans le menu Actions."
        )
    ).to_be_visible()
    expect(page.get_by_role("button", name="Publier l'événement")).to_be_visible()


def test_publish_and_notifier_ac_show_modal(live_server, page: Page):
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("button", name="Publier et déclarer à l'AC").click()

    expect(page.get_by_role("heading", name="Notifier à l'AC l'événement ")).to_be_visible()
    expect(
        page.get_by_text(
            "Un message automatique va être envoyé à l'administration centrale pour l'informer de cette notification. Confirmez-vous la déclaration de cet événement ?"
        )
    ).to_be_visible()
    expect(
        page.get_by_label("Notifier à l'AC l'événement").get_by_role("button", name="Publier et déclarer à l'AC")
    ).to_be_visible()


@pytest.mark.django_db
def test_can_publish_and_notifier_ac(live_server, page: Page, mailoutbox):
    ContactStructureFactory(structure__niveau1=AC_STRUCTURE, structure__niveau2=MUS_STRUCTURE)
    ContactStructureFactory(structure__niveau1=AC_STRUCTURE, structure__niveau2=BSV_STRUCTURE)
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("button", name="Publier et déclarer à l'AC").click()
    page.get_by_label("Notifier à l'AC l'événement").get_by_role("button", name="Publier et déclarer à l'AC").click()

    expect(page.get_by_text(f"Événement {evenement.numero} publié avec succès")).to_be_visible()
    expect(page.get_by_text("L'administration centrale a été notifiée avec succès")).to_be_visible()
    expect(page.get_by_text("Déclaré AC")).to_be_visible()
    evenement.refresh_from_db()
    assert evenement.is_published is True
    assert evenement.is_ac_notified is True
    assert len(mailoutbox) == 1


@pytest.mark.django_db
def test_cant_publish_and_notifier_ac_evenement_i_cant_see(client, mailoutbox):
    evenement = EvenementFactory(createur=StructureFactory(), etat=Evenement.Etat.BROUILLON)
    response = client.get(evenement.get_absolute_url())
    assert response.status_code == 403

    payload = {
        "content_type_id": ContentType.objects.get_for_model(evenement).id,
        "content_id": evenement.pk,
    }
    response = client.post(reverse("publish-and-ac-notification"), data=payload)

    assert response.status_code == 302
    evenement.refresh_from_db()
    assert evenement.is_draft is True
    assert evenement.is_ac_notified is False
    assert len(mailoutbox) == 0


def test_show_only_publish_btn_and_not_show_modal_for_ac_users(
    live_server, page: Page, mocked_authentification_user, contact_ac
):
    contact_structure_mus = ContactStructureFactory(structure__niveau1=AC_STRUCTURE, structure__niveau2=MUS_STRUCTURE)
    mocked_authentification_user.agent.structure = contact_structure_mus.structure
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON, createur=contact_structure_mus.structure)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    expect(page.get_by_role("button", name="Publier", exact=True)).to_be_visible()
    expect(page.get_by_role("button", name="Publier sans déclarer à l'AC")).not_to_be_visible()
    expect(page.get_by_role("button", name="Publier et déclarer à l'AC")).not_to_be_visible()

    page.get_by_role("button", name="Publier").click()
    expect(page.get_by_text(f"Événement {evenement.numero} publié avec succès")).to_be_visible()
