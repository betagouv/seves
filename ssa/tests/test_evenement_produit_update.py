from playwright.sync_api import expect

from core.factories import StructureFactory
from core.models import LienLibre
from ssa.factories import EvenementProduitFactory
from ssa.models import EvenementProduit
from ssa.tests.pages import EvenementProduitFormPage


def test_can_update_evenement_produit_descripteur_and_save_as_draft(
    live_server, page, choice_js_get_values, choice_js_fill
):
    evenement: EvenementProduit = EvenementProduitFactory(numeros_rappel_conso=["2000-01-1111"])
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
    assert choice_js_get_values(page, "#id_free_link") == [f"Événement produit : {for_free_link.numero}Remove item"]
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
    evenement: EvenementProduit = EvenementProduitFactory()
    update_page = EvenementProduitFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)
    update_page.description.fill("New value")
    update_page.publish()

    expect(update_page.page.get_by_text("L'événement produit a bien été modifié.")).to_be_visible()
    evenement.refresh_from_db()
    assert evenement.is_published is True
    assert evenement.description == "New value"


def test_update_evenement_produit_will_not_change_createur(live_server, page):
    createur = StructureFactory()
    evenement: EvenementProduit = EvenementProduitFactory(createur=createur, etat=EvenementProduit.Etat.EN_COURS)
    update_page = EvenementProduitFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)
    update_page.description.fill("New value")
    update_page.publish()

    expect(update_page.page.get_by_text("L'événement produit a bien été modifié.")).to_be_visible()
    evenement.refresh_from_db()
    assert evenement.createur == createur


def test_update_adds_agent_and_structure_to_contacts(live_server, page, mocked_authentification_user):
    createur = StructureFactory()
    evenement: EvenementProduit = EvenementProduitFactory(createur=createur, etat=EvenementProduit.Etat.EN_COURS)
    assert evenement.contacts.count() == 0

    update_page = EvenementProduitFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)
    update_page.description.fill("New value")
    update_page.publish()

    expect(update_page.page.get_by_text("L'événement produit a bien été modifié.")).to_be_visible()
    evenement.refresh_from_db()
    assert evenement.contacts.count() == 2
    assert mocked_authentification_user.agent.contact_set.get() in evenement.contacts.all()
    assert mocked_authentification_user.agent.structure.contact_set.get() in evenement.contacts.all()
