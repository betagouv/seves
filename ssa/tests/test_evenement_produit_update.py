import pytest
from playwright.sync_api import expect

from core.factories import StructureFactory, DepartementFactory, ContactStructureFactory, ContactAgentFactory
from core.mixins import WithEtatMixin
from core.models import LienLibre
from ssa.factories import EvenementProduitFactory, EtablissementFactory
from ssa.models import EvenementProduit, Etablissement
from ssa.constants import CategorieDanger, CategorieProduit, TypeEvenement
from ssa.tests.pages import EvenementProduitFormPage
from ssa.tests.test_evenement_produit_creation import FIELD_TO_EXCLUDE_ETABLISSEMENT


def test_can_update_evenement_produit_descripteur_and_save_as_draft(
    live_server, page, choice_js_get_values, choice_js_fill, mus_contact
):
    evenement: EvenementProduit = EvenementProduitFactory(numeros_rappel_conso=["2000-01-1111"], not_bacterie=True)
    wanted_values = EvenementProduitFactory.build()
    for_free_link = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    for_other_free_link = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    LienLibre.objects.create(related_object_1=evenement, related_object_2=for_free_link)

    update_page = EvenementProduitFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)

    expect(update_page.date_creation).to_have_value(evenement.date_creation.strftime("%d/%m/%Y"))

    inputs_fields = [
        "description",
        "denomination",
        "marque",
        "lots",
        "description_complementaire",
        "precision_danger",
        "quantification",
        "evaluation",
        "reference_souches",
        "reference_clusters",
    ]
    select_fields = ["type_evenement", "source", "actions_engagees"]

    # We need to check all the values *before* we make any changes because some field resets when there is a change
    for field in inputs_fields + select_fields:
        expect(getattr(update_page, field)).to_have_value(str(getattr(evenement, field)))

    expect(update_page.numero_rasff).not_to_be_visible()

    assert choice_js_get_values(page, "#id_quantification_unite") == [evenement.get_quantification_unite_display()]
    assert choice_js_get_values(page, "#id_free_link") == [f"{for_free_link.numero}Remove item"]
    expect(update_page.page.get_by_text("2000-01-1111", exact=True)).to_be_visible()

    assert update_page.get_treeselect_options("categorie-danger") == [
        evenement.get_categorie_danger_display().split(">")[-1].strip()
    ]
    assert update_page.get_treeselect_options("categorie-produit") == [
        evenement.get_categorie_produit_display().split(">")[-1].strip()
    ]

    # Making changes on all fields
    for field in inputs_fields:
        getattr(update_page, field).fill(getattr(wanted_values, field))

    for field in select_fields:
        getattr(update_page, field).select_option(getattr(wanted_values, field))

    update_page.set_categorie_produit(wanted_values, clear_input=True)
    update_page.set_categorie_danger(wanted_values, clear_input=True)

    update_page.delete_rappel_conso("2000-01-1111")
    update_page.add_rappel_conso("2025-12-1212")
    update_page.add_free_link(for_other_free_link.numero, choice_js_fill)

    update_page.submit_as_draft()
    expect(update_page.page.get_by_text("L'événement produit a bien été modifié.")).to_be_visible()

    evenement.refresh_from_db()
    assert evenement.is_draft is True

    for field in inputs_fields + select_fields:
        assert getattr(evenement, field) == getattr(wanted_values, field), f"Failed on field : {field}"

    assert evenement.categorie_produit == wanted_values.categorie_produit
    assert evenement.categorie_danger == wanted_values.categorie_danger
    assert evenement.numeros_rappel_conso == ["2025-12-1212"]

    assert LienLibre.objects.count() == 2
    assert [lien.related_object_1 for lien in LienLibre.objects.all()] == [evenement, evenement]
    expected = sorted([for_free_link.numero, for_other_free_link.numero])
    assert sorted([lien.related_object_2.numero for lien in LienLibre.objects.all()]) == expected


def test_can_update_evenement_produit_descripteur_and_publish(live_server, page):
    evenement: EvenementProduit = EvenementProduitFactory(not_bacterie=True)
    update_page = EvenementProduitFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)
    update_page.description.fill("New value")
    update_page.publish()

    expect(update_page.page.get_by_text("L'événement produit a bien été modifié.")).to_be_visible()
    evenement.refresh_from_db()
    assert evenement.is_published is True
    assert evenement.description == "New value"


def test_contact_added_to_evenement_when_edit(live_server, page, mocked_authentification_user):
    evenement: EvenementProduit = EvenementProduitFactory(
        createur=StructureFactory(), etat=EvenementProduit.Etat.EN_COURS, not_bacterie=True
    )
    assert evenement.contacts.count() == 0
    update_page = EvenementProduitFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)
    update_page.description.fill("New value")
    update_page.publish()

    expect(update_page.page.get_by_text("L'événement produit a bien été modifié.")).to_be_visible()
    assert evenement.contacts.count() == 2
    assert mocked_authentification_user.agent.contact_set.get() in evenement.contacts.all()
    assert mocked_authentification_user.agent.structure.contact_set.get() in evenement.contacts.all()


def test_update_evenement_produit_will_not_change_createur(live_server, page):
    createur = StructureFactory()
    evenement: EvenementProduit = EvenementProduitFactory(
        createur=createur, not_bacterie=True, etat=EvenementProduit.Etat.EN_COURS
    )
    update_page = EvenementProduitFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)
    update_page.description.fill("New value")
    update_page.publish()

    expect(update_page.page.get_by_text("L'événement produit a bien été modifié.")).to_be_visible()
    evenement.refresh_from_db()
    assert evenement.createur == createur


def test_update_adds_agent_and_structure_to_contacts(live_server, page, mocked_authentification_user):
    createur = StructureFactory()
    evenement: EvenementProduit = EvenementProduitFactory(
        createur=createur, not_bacterie=True, etat=EvenementProduit.Etat.EN_COURS
    )
    structure = ContactStructureFactory()
    agent = ContactAgentFactory()
    evenement.contacts.add(structure)
    evenement.contacts.add(agent)
    assert evenement.contacts.count() == 2

    update_page = EvenementProduitFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)
    update_page.description.fill("New value")
    update_page.publish()

    expect(update_page.page.get_by_text("L'événement produit a bien été modifié.")).to_be_visible()
    evenement.refresh_from_db()
    assert set(evenement.contacts.all()) == {
        agent,
        structure,
        mocked_authentification_user.agent.contact_set.get(),
        mocked_authentification_user.agent.structure.contact_set.get(),
    }


def test_can_update_evenement_danger_that_had_pam_info_to_not_bacterie(live_server, page):
    evenement: EvenementProduit = EvenementProduitFactory(bacterie=True)
    update_page = EvenementProduitFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)
    update_page.clear_treeselect("categorie-danger")
    update_page.set_categorie_danger_from_shortcut("Résidu de Pesticide Biocide")

    update_page.publish()

    expect(update_page.page.get_by_text("L'événement produit a bien été modifié.")).to_be_visible()
    evenement.refresh_from_db()
    assert evenement.categorie_danger == CategorieDanger.RESIDU_DE_PESTICIDE_BIOCIDE
    assert evenement.produit_pret_a_manger == ""


def test_can_see_and_edit_etablissement_on_evenement_produit_update(
    live_server, page, settings, assert_models_are_equal, assert_etablissement_card_is_correct
):
    settings.SIRENE_CONSUMER_KEY = "FOO"
    settings.SIRENE_CONSUMER_SECRET = "BAR"
    evenement: EvenementProduit = EvenementProduitFactory(not_bacterie=True)
    etablissement_1 = EtablissementFactory(evenement_produit=evenement)
    etablissement_2 = EtablissementFactory(evenement_produit=evenement)

    departement = DepartementFactory()
    wanted_values = EtablissementFactory.build(departement=departement)

    update_page = EvenementProduitFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)

    etablissement_card = update_page.etablissement_card()
    assert_etablissement_card_is_correct(etablissement_card, etablissement_1)

    etablissement_card = update_page.etablissement_card(index=1)
    assert_etablissement_card_is_correct(etablissement_card, etablissement_2)

    update_page.edit_etablissement_with_new_values(index=0, wanted_values=wanted_values)

    etablissement_card = update_page.etablissement_card()
    assert_etablissement_card_is_correct(etablissement_card, wanted_values)

    update_page.publish()

    assert evenement.etablissements.count() == 2
    assert evenement.etablissements.last() == etablissement_2
    assert_models_are_equal(evenement.etablissements.first(), wanted_values, to_exclude=FIELD_TO_EXCLUDE_ETABLISSEMENT)


def test_can_add_etablissement_on_evenement_produit_update(live_server, page, settings, assert_models_are_equal):
    settings.SIRENE_CONSUMER_KEY = "FOO"
    settings.SIRENE_CONSUMER_SECRET = "BAR"
    evenement: EvenementProduit = EvenementProduitFactory(not_bacterie=True)
    EtablissementFactory(evenement_produit=evenement)
    departement = DepartementFactory()
    wanted_values = EtablissementFactory.build(departement=departement)

    update_page = EvenementProduitFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)

    update_page.add_etablissement(wanted_values)
    update_page.publish()

    assert evenement.etablissements.count() == 2
    assert_models_are_equal(evenement.etablissements.last(), wanted_values, to_exclude=FIELD_TO_EXCLUDE_ETABLISSEMENT)


def test_can_delete_etablissement_on_evenement_produit_update(live_server, page, assert_models_are_equal):
    evenement: EvenementProduit = EvenementProduitFactory(not_bacterie=True)
    to_keep = EtablissementFactory(evenement_produit=evenement)
    _to_delete = EtablissementFactory(evenement_produit=evenement)

    update_page = EvenementProduitFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)

    update_page.delete_etablissement(index=1)
    update_page.publish()

    assert evenement.etablissements.count() == 1
    assert_models_are_equal(evenement.etablissements.last(), to_keep, to_exclude=FIELD_TO_EXCLUDE_ETABLISSEMENT)


def test_can_udpate_etablissement_with_error_show_message(live_server, page, assert_models_are_equal):
    evenement: EvenementProduit = EvenementProduitFactory(not_bacterie=True)
    etablissement = EtablissementFactory(evenement_produit=evenement)

    update_page = EvenementProduitFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)
    update_page.page.evaluate("""() => {
        const agrementInput = document.querySelector('#id_etablissements-0-numero_agrement');
        agrementInput.removeAttribute('pattern');
        agrementInput.value = "22"
    }""")
    update_page.publish(wait_for=evenement.get_update_url())
    expect(
        update_page.page.get_by_text(
            "Erreur dans le formulaire établissement #1 : 'numero_agrement': 22 n'est pas un format valide.", exact=True
        )
    ).to_be_visible()

    assert Etablissement.objects.get().numero_agrement == etablissement.numero_agrement


def test_can_update_and_handle_rappel_conso_on_publised_evenement_produit(live_server, page):
    evenement: EvenementProduit = EvenementProduitFactory(
        numeros_rappel_conso=["2000-01-1111"], not_bacterie=True, etat=EvenementProduit.Etat.EN_COURS
    )

    update_page = EvenementProduitFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)
    expect(update_page.page.get_by_text("2000-01-1111", exact=True)).to_be_visible()
    update_page.delete_rappel_conso("2000-01-1111")
    update_page.add_rappel_conso("2025-12-1212")
    update_page.publish()
    expect(update_page.page.get_by_text("L'événement produit a bien été modifié.")).to_be_visible()

    evenement.refresh_from_db()
    assert evenement.numeros_rappel_conso == ["2025-12-1212"]


def test_display_of_notices(live_server, mocked_authentification_user, page):
    evenement: EvenementProduit = EvenementProduitFactory(
        categorie_produit=CategorieProduit.OVOPRODUIT, categorie_danger=CategorieDanger.BACILLUS
    )
    update_page = EvenementProduitFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)
    expected_text = "Catégorie de niveau 2 sélectionnée : pensez à préciser dès que possible."

    expect(update_page.page.locator("#notice-container-produit").get_by_text(expected_text)).to_be_visible()
    expect(update_page.page.locator("#notice-container-risque").get_by_text(expected_text)).to_be_visible()


def test_update_type_evenement_will_trigger_email(
    live_server, page, mailoutbox, mocked_authentification_user, mus_contact
):
    evenement: EvenementProduit = EvenementProduitFactory(
        not_bacterie=True, type_evenement=TypeEvenement.NON_ALERTE, etat=WithEtatMixin.Etat.EN_COURS
    )
    update_page = EvenementProduitFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)
    update_page.type_evenement.select_option(TypeEvenement.ALERTE_PRODUIT_NATIONALE)
    update_page.publish()

    expect(update_page.page.get_by_text("L'événement produit a bien été modifié.")).to_be_visible()
    evenement.refresh_from_db()
    assert evenement.type_evenement == TypeEvenement.ALERTE_PRODUIT_NATIONALE
    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.to == [mus_contact.email, mocked_authentification_user.agent.contact_set.get().email]
    assert evenement.numero in mail.subject
    assert "Modification type d’évènement" in mail.subject
    assert mocked_authentification_user.agent.agent_with_structure in mail.body


def test_update_aliments_animaux_will_trigger_email(live_server, page, mailoutbox, mocked_authentification_user):
    evenement: EvenementProduit = EvenementProduitFactory(
        not_bacterie=True, aliments_animaux=None, etat=WithEtatMixin.Etat.EN_COURS
    )
    other_structure_contact = ContactStructureFactory()
    evenement.contacts.add(other_structure_contact)
    update_page = EvenementProduitFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)
    update_page.set_aliments_animaux("Oui")
    update_page.publish()

    expect(update_page.page.get_by_text("L'événement produit a bien été modifié.")).to_be_visible()
    evenement.refresh_from_db()
    assert evenement.aliments_animaux is True
    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.to == [other_structure_contact.email]
    assert evenement.numero in mail.subject
    assert "Inclut des aliments pour animaux" in mail.subject
    assert "inclut désormais des aliments pour animaux." in mail.body


def test_update_reference_souches_will_trigger_email(live_server, page, mailoutbox, mocked_authentification_user):
    evenement: EvenementProduit = EvenementProduitFactory(
        not_bacterie=True, reference_souches="Test", etat=WithEtatMixin.Etat.EN_COURS
    )
    other_agent_contact = ContactAgentFactory()
    evenement.contacts.add(other_agent_contact)
    update_page = EvenementProduitFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)
    update_page.reference_souches.fill("New value")
    update_page.publish()

    expect(update_page.page.get_by_text("L'événement produit a bien été modifié.")).to_be_visible()
    evenement.refresh_from_db()
    assert evenement.reference_souches == "New value"
    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.to == [other_agent_contact.email]
    assert evenement.numero in mail.subject
    assert "Souche / cluster" in mail.subject
    assert "Référence souche : New value" in mail.body


def test_update_reference_clusters_will_trigger_email(live_server, page, mailoutbox, mocked_authentification_user):
    evenement: EvenementProduit = EvenementProduitFactory(
        not_bacterie=True, reference_clusters="Test", etat=WithEtatMixin.Etat.EN_COURS
    )
    other_agent_contact = ContactAgentFactory()
    evenement.contacts.add(other_agent_contact)
    update_page = EvenementProduitFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)
    update_page.reference_clusters.fill("New value")
    update_page.publish()

    expect(update_page.page.get_by_text("L'événement produit a bien été modifié.")).to_be_visible()
    evenement.refresh_from_db()
    assert evenement.reference_clusters == "New value"
    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.to == [other_agent_contact.email]
    assert evenement.numero in mail.subject
    assert "Souche / cluster" in mail.subject
    assert "Référence cluster : New value" in mail.body


@pytest.mark.django_db
def test_update_evenement_produit_performances(client, django_assert_num_queries):
    evenement: EvenementProduit = EvenementProduitFactory(numeros_rappel_conso=["2000-01-1111"], not_bacterie=True)

    with django_assert_num_queries(15):
        client.get(evenement.get_update_url())


def test_evenement_produit_update_has_locking_protection(
    live_server,
    page,
    mocked_authentification_user,
):
    evenement = EvenementProduitFactory(description="AAA")
    update_page = EvenementProduitFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)
    update_page.description.fill("BBB")

    evenement.description = "CCC"
    evenement.save()

    update_page.publish(wait_for="modification")

    evenement.refresh_from_db()
    assert evenement.description == "CCC"
    initial_timestamp = page.evaluate("performance.timing.navigationStart")
    expect(
        page.get_by_text(
            "Vos modifications n'ont pas été enregistrées. Un autre utilisateur a modifié cet objet. Fermer cette modale pour charger la dernière version."
        )
    ).to_be_visible()
    page.keyboard.press("Escape")
    page.wait_for_function(f"performance.timing.navigationStart > {initial_timestamp}")
