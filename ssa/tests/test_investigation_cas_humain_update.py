from django.urls import reverse
from playwright.sync_api import expect

from core.factories import StructureFactory, DepartementFactory, ContactStructureFactory, ContactAgentFactory
from core.mixins import WithEtatMixin
from core.models import LienLibre
from ssa.factories import InvestigationCasHumainFactory, EtablissementFactory
from ssa.models import EvenementInvestigationCasHumain, Etablissement
from ssa.tests.pages import InvestigationCasHumainFormPage
from ssa.tests.test_investigation_cas_humain_creation import FIELD_TO_EXCLUDE_ETABLISSEMENT


def test_can_update_investigation_cas_humain_descripteur_and_save_as_draft(
    live_server, page, choice_js_get_values, choice_js_fill
):
    evenement: EvenementInvestigationCasHumain = InvestigationCasHumainFactory()
    wanted_values = InvestigationCasHumainFactory.build()
    for_free_link = InvestigationCasHumainFactory(etat=WithEtatMixin.Etat.EN_COURS)
    for_other_free_link = InvestigationCasHumainFactory(etat=WithEtatMixin.Etat.EN_COURS)
    LienLibre.objects.create(related_object_1=evenement, related_object_2=for_free_link)

    update_page = InvestigationCasHumainFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)

    expect(update_page.date_reception).to_have_value(evenement.date_reception.strftime("%Y-%m-%d"))

    inputs_fields = [
        "evaluation",
        "reference_souches",
        "reference_clusters",
    ]
    select_fields = ["source"]

    # We need to check all the values *before* we make any changes because some field resets when there is a change
    for field in inputs_fields + select_fields:
        expect(getattr(update_page, field)).to_have_value(str(getattr(evenement, field)))

    expect(update_page.numero_rasff).not_to_be_visible()

    assert choice_js_get_values(page, "#id_free_link") == [
        f"Investigation de cas humain : {for_free_link.numero}Remove item"
    ]

    # Making changes on all fields
    for field in inputs_fields:
        getattr(update_page, field).fill(getattr(wanted_values, field))

    for field in select_fields:
        getattr(update_page, field).select_option(getattr(wanted_values, field))

    update_page.add_free_link(for_other_free_link.numero, choice_js_fill)

    update_page.submit_as_draft()
    expect(update_page.page.get_by_text("L'évènement Investigation cas humain a bien été modifié.")).to_be_visible()

    evenement.refresh_from_db()
    assert evenement.is_draft is True

    for field in inputs_fields + select_fields:
        assert getattr(evenement, field) == getattr(wanted_values, field), f"Failed on field : {field}"

    assert LienLibre.objects.count() == 2
    assert [lien.related_object_1 for lien in LienLibre.objects.all()] == [evenement, evenement]
    expected = sorted([for_free_link.numero, for_other_free_link.numero])
    assert sorted([lien.related_object_2.numero for lien in LienLibre.objects.all()]) == expected


def test_can_update_investigation_cas_humain_descripteur_and_publish(live_server, page):
    evenement: EvenementInvestigationCasHumain = InvestigationCasHumainFactory()
    update_page = InvestigationCasHumainFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)
    update_page.description.fill("New value")
    update_page.publish()

    expect(update_page.page.get_by_text("L'évènement Investigation cas humain a bien été modifié.")).to_be_visible()
    evenement.refresh_from_db()
    assert evenement.is_published is True
    assert evenement.description == "New value"


def test_update_investigation_cas_humain_will_not_change_createur(live_server, page):
    createur = StructureFactory()
    evenement: EvenementInvestigationCasHumain = InvestigationCasHumainFactory(
        createur=createur, etat=WithEtatMixin.Etat.EN_COURS
    )
    update_page = InvestigationCasHumainFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)
    update_page.description.fill("New value")
    update_page.publish()

    expect(update_page.page.get_by_text("L'évènement Investigation cas humain a bien été modifié.")).to_be_visible()
    evenement.refresh_from_db()
    assert evenement.createur == createur


def test_can_see_and_edit_etablissement_on_investigation_cas_humain_update(
    live_server, page, settings, assert_models_are_equal, assert_etablissement_card_is_correct
):
    settings.SIRENE_CONSUMER_KEY = "FOO"
    settings.SIRENE_CONSUMER_SECRET = "BAR"
    evenement: EvenementInvestigationCasHumain = InvestigationCasHumainFactory()
    etablissement_1 = EtablissementFactory(investigation_cas_humain=evenement)
    etablissement_2 = EtablissementFactory(investigation_cas_humain=evenement)

    departement = DepartementFactory()
    wanted_values = EtablissementFactory.build(investigation_cas_humain=evenement, departement=departement)

    update_page = InvestigationCasHumainFormPage(page, live_server.url)
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


def test_can_add_etablissement_on_investigation_cas_humain_update(live_server, page, settings, assert_models_are_equal):
    settings.SIRENE_CONSUMER_KEY = "FOO"
    settings.SIRENE_CONSUMER_SECRET = "BAR"
    evenement: EvenementInvestigationCasHumain = InvestigationCasHumainFactory()
    EtablissementFactory(investigation_cas_humain=evenement)
    departement = DepartementFactory()
    wanted_values = EtablissementFactory.build(investigation_cas_humain=evenement, departement=departement)

    update_page = InvestigationCasHumainFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)

    update_page.add_etablissement(wanted_values)
    update_page.publish()

    assert evenement.etablissements.count() == 2
    assert_models_are_equal(evenement.etablissements.last(), wanted_values, to_exclude=FIELD_TO_EXCLUDE_ETABLISSEMENT)


def test_can_delete_etablissement_on_investigation_cas_humain_update(live_server, page, assert_models_are_equal):
    evenement: EvenementInvestigationCasHumain = InvestigationCasHumainFactory()
    to_keep = EtablissementFactory(investigation_cas_humain=evenement)
    _to_delete = EtablissementFactory(investigation_cas_humain=evenement)

    update_page = InvestigationCasHumainFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)

    update_page.delete_etablissement(index=1)
    update_page.publish()

    assert evenement.etablissements.count() == 1
    assert_models_are_equal(evenement.etablissements.last(), to_keep, to_exclude=FIELD_TO_EXCLUDE_ETABLISSEMENT)


def test_can_udpate_etablissement_with_error_show_message(live_server, page, assert_models_are_equal):
    evenement: EvenementInvestigationCasHumain = InvestigationCasHumainFactory()
    etablissement = EtablissementFactory(investigation_cas_humain=evenement)

    update_page = InvestigationCasHumainFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)
    update_page.page.evaluate("""() => {
        const agrementInput = document.querySelector('#id_etablissements-0-numero_agrement');
        agrementInput.removeAttribute('pattern');
        agrementInput.value = "22"
    }""")
    update_page.publish(wait_for=reverse("ssa:investigation-cas-humain-update", kwargs={"pk": evenement.pk}))
    expect(
        update_page.page.get_by_text(
            "Erreur dans le formulaire établissement #1 : 'numero_agrement': 22 n'est pas un format valide.", exact=True
        )
    ).to_be_visible()

    assert Etablissement.objects.get().numero_agrement == etablissement.numero_agrement


def test_contact_added_to_investigation_cas_humain_when_edit(live_server, page, mocked_authentification_user):
    evenement = InvestigationCasHumainFactory(
        createur=StructureFactory(), etat=EvenementInvestigationCasHumain.Etat.EN_COURS, not_bacterie=True
    )
    assert evenement.contacts.count() == 0
    update_page = InvestigationCasHumainFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)
    update_page.description.fill("New value")
    update_page.publish()

    expect(update_page.page.get_by_text("L'évènement Investigation cas humain a bien été modifié.")).to_be_visible()
    assert evenement.contacts.count() == 2
    assert mocked_authentification_user.agent.contact_set.get() in evenement.contacts.all()
    assert mocked_authentification_user.agent.structure.contact_set.get() in evenement.contacts.all()


def test_update_adds_agent_and_structure_to_contacts(live_server, page, mocked_authentification_user):
    createur = StructureFactory()
    evenement = InvestigationCasHumainFactory(
        createur=createur, not_bacterie=True, etat=EvenementInvestigationCasHumain.Etat.EN_COURS
    )
    structure = ContactStructureFactory()
    agent = ContactAgentFactory()
    evenement.contacts.add(structure)
    evenement.contacts.add(agent)
    assert evenement.contacts.count() == 2

    update_page = InvestigationCasHumainFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)
    update_page.description.fill("New value")
    update_page.publish()

    expect(update_page.page.get_by_text("L'évènement Investigation cas humain a bien été modifié.")).to_be_visible()
    evenement.refresh_from_db()
    assert set(evenement.contacts.all()) == {
        agent,
        structure,
        mocked_authentification_user.agent.contact_set.get(),
        mocked_authentification_user.agent.structure.contact_set.get(),
    }


def test_update_reference_souches_will_trigger_email(live_server, page, mailoutbox, mocked_authentification_user):
    evenement = InvestigationCasHumainFactory(
        not_bacterie=True, reference_souches="Test", etat=WithEtatMixin.Etat.EN_COURS
    )
    other_agent_contact = ContactAgentFactory()
    evenement.contacts.add(other_agent_contact)
    update_page = InvestigationCasHumainFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)
    update_page.reference_souches.fill("New value")
    update_page.publish()

    expect(update_page.page.get_by_text("L'évènement Investigation cas humain a bien été modifié.")).to_be_visible()
    evenement.refresh_from_db()
    assert evenement.reference_souches == "New value"
    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.to == [other_agent_contact.email]
    assert evenement.numero in mail.subject
    assert "Souche / cluster" in mail.subject
    assert "Référence souche : New value" in mail.body


def test_update_reference_clusters_will_trigger_email(live_server, page, mailoutbox, mocked_authentification_user):
    evenement = InvestigationCasHumainFactory(
        not_bacterie=True, reference_clusters="Test", etat=WithEtatMixin.Etat.EN_COURS
    )
    other_agent_contact = ContactAgentFactory()
    evenement.contacts.add(other_agent_contact)
    update_page = InvestigationCasHumainFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)
    update_page.reference_clusters.fill("New value")
    update_page.publish()

    expect(update_page.page.get_by_text("L'évènement Investigation cas humain a bien été modifié.")).to_be_visible()
    evenement.refresh_from_db()
    assert evenement.reference_clusters == "New value"
    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.to == [other_agent_contact.email]
    assert evenement.numero in mail.subject
    assert "Souche / cluster" in mail.subject
    assert "Référence cluster : New value" in mail.body


def test_investigation_cas_humain_update_has_locking_protection(
    live_server,
    page,
    mocked_authentification_user,
):
    evenement = InvestigationCasHumainFactory(description="AAA")
    update_page = InvestigationCasHumainFormPage(page, live_server.url)
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
