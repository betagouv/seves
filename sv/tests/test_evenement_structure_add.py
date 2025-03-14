import pytest
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from playwright.sync_api import expect

from core.factories import ContactStructureFactory
from sv.factories import EvenementFactory
from sv.models import Evenement


@pytest.fixture
def contacts_structure():
    return ContactStructureFactory.create_batch(2, with_one_active_agent=True)


@pytest.mark.django_db
def test_add_structure_form_hides_empty_emails(live_server, page):
    evenement = EvenementFactory()
    evenement.contacts.set(ContactStructureFactory.create_batch(5, with_one_active_agent=True))

    ContactStructureFactory(structure__libelle="Level 1", with_one_active_agent=True)
    ContactStructureFactory(structure__libelle="Level 2", with_one_active_agent=True, email="")
    ContactStructureFactory(structure__libelle="Level 3", with_one_active_agent=True)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.query_selector("#add-contact-structure-form .choices").click()

    expect(page.get_by_label("Contacts").get_by_role("option", name="Level 1")).to_be_visible()
    expect(page.get_by_label("Contacts").get_by_role("option", name="Level 2")).not_to_be_visible()
    expect(page.get_by_label("Contacts").get_by_role("option", name="Level 3")).to_be_visible()


@pytest.mark.django_db
def test_add_structure_form_hides_structure_without_active_user(live_server, page):
    visible_structure = ContactStructureFactory(with_one_active_agent=True)
    unvisible_structure = ContactStructureFactory()

    page.goto(f"{live_server.url}{EvenementFactory().get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.query_selector("#add-contact-structure-form .choices").click()

    expect(page.get_by_label("Contacts").get_by_role("option", name=str(visible_structure.structure))).to_be_visible()
    expect(
        page.get_by_label("Contacts").get_by_role("option", name=str(unvisible_structure.structure))
    ).not_to_be_visible()


@pytest.mark.django_db
def test_add_structure_form_service_account_is_hidden(live_server, page):
    page.goto(f"{live_server.url}/{EvenementFactory().get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.query_selector("#add-contact-structure-form .choices").click()
    expect(page.get_by_text("service_account")).not_to_be_visible()


@pytest.mark.django_db
def test_structure_niveau2_without_emails_are_not_visible(live_server, page):
    ContactStructureFactory(structure__niveau1="Level 1", structure__libelle="Foo", with_one_active_agent=True)
    ContactStructureFactory(
        structure__niveau1="Level 1", structure__libelle="Bar", with_one_active_agent=True, email=""
    )
    page.goto(f"{live_server.url}/{EvenementFactory().get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.query_selector("#add-contact-structure-form .choices").click()

    expect(page.get_by_label("Contacts").get_by_role("option", name="Foo")).to_be_visible()
    expect(page.get_by_label("Contacts").get_by_role("option", name="Bar")).not_to_be_visible()


@pytest.mark.django_db
def test_add_structure_to_an_evenement(live_server, page, choice_js_fill):
    contact = ContactStructureFactory(with_one_active_agent=True)
    evenement = EvenementFactory()

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    choice_js_fill(page, "#add-contact-structure-form .choices", str(contact), str(contact))
    page.locator("#add-contact-structure-form").get_by_role("button", name="Ajouter").click()
    page.get_by_role("tab", name="Contacts").click()

    expect(page.get_by_text("La structure a été ajoutée avec succès.")).to_be_visible()
    expect(page.get_by_test_id("contacts-structures")).to_be_visible()
    assert page.get_by_test_id("contacts-structures").count() == 1
    assert Evenement.objects.filter(pk=evenement.pk, contacts=contact).exists()


@pytest.mark.django_db
def test_add_multiple_structures_to_an_evenement(live_server, page, choice_js_fill):
    contact_structure_1, contact_structure_2 = ContactStructureFactory.create_batch(2, with_one_active_agent=True)
    evenement = EvenementFactory()

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    choice_js_fill(page, "#add-contact-structure-form .choices", str(contact_structure_1), str(contact_structure_1))
    choice_js_fill(page, "#add-contact-structure-form .choices", str(contact_structure_2), str(contact_structure_2))
    page.locator("#add-contact-structure-form").get_by_role("button", name="Ajouter").click()

    expect(page.get_by_text("Les 2 structures ont été ajoutées avec succès.")).to_be_visible()
    page.get_by_role("tab", name="Contacts").click()
    assert page.get_by_test_id("contacts-structures").count() == 2
    expect(page.get_by_test_id("contacts-structures").get_by_text(str(contact_structure_1), exact=True)).to_be_visible()
    expect(page.get_by_test_id("contacts-structures").get_by_text(str(contact_structure_2), exact=True)).to_be_visible()


@pytest.mark.django_db
def test_cant_add_contact_structure_if_evenement_brouillon(client):
    contact = ContactStructureFactory(with_one_active_agent=True)
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON)

    response = client.post(
        reverse("structure-add"),
        data={
            "contacts_structures": [contact.id],
            "content_type_id": ContentType.objects.get_for_model(evenement).id,
            "content_id": evenement.id,
        },
        follow=True,
    )

    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert messages[0].level_tag == "error"
    assert str(messages[0]) == "Action impossible car la fiche est en brouillon"
