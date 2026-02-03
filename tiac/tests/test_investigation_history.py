from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from playwright.sync_api import expect

from core.factories import MessageFactory, DepartementFactory
from core.models import LienLibre
from tiac.factories import (
    InvestigationTiacFactory,
    EtablissementFactory,
    RepasSuspectFactory,
    AlimentSuspectFactory,
    AnalyseAlimentaireFactory,
)
from tiac.models import InvestigationTiac
from tiac.tests.pages import (
    InvestigationTiacEditPage,
)


def test_can_view_investigation_tiac_history(live_server, page, mus_contact):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)

    message = MessageFactory(content_object=evenement)
    message.is_deleted = True
    message.save()

    departement = DepartementFactory()
    etablissement = EtablissementFactory.build(departement=departement)
    departement = DepartementFactory()
    repas = RepasSuspectFactory.build(departement=departement)
    aliment = AlimentSuspectFactory.build(simple=True)
    analyse = AnalyseAlimentaireFactory.build()

    edit_page = InvestigationTiacEditPage(page, live_server.url, evenement)
    edit_page.navigate()
    edit_page.add_etablissement(etablissement)
    edit_page.add_repas(repas)
    edit_page.add_analyse_alimentaire(analyse)
    edit_page.add_aliment_simple(aliment)
    edit_page.submit()

    other_evenement = InvestigationTiacFactory()
    lien = LienLibre.objects.create(related_object_1=other_evenement, related_object_2=evenement)
    lien.delete()

    content_type = ContentType.objects.get_for_model(InvestigationTiac)
    url = reverse("revision-list", kwargs={"content_type": content_type.pk, "pk": evenement.pk})
    page.goto(f"{live_server.url}{url}")

    expect(page.locator("tr")).to_have_count(
        len(
            [
                "One for table header",
                "One (fake) line for the creation of the object",
                "One for the deletion of the message",
                "One for creation of the LienLibre",
                "One for deletion of the LienLibre",
                "One for the etablissement that is added",
                "One for the repas that is added",
                "One for the analyse that is added",
                "One for the aliment that is added",
                "One for the contact added while editing the object",
            ]
        )
    )

    expect(page.get_by_text(f"Le lien '{str(other_evenement)}' a été ajouté à la fiche", exact=True)).to_be_visible()
    expect(page.get_by_text(f"Le lien '{str(other_evenement)}' a été supprimé à la fiche", exact=True)).to_be_visible()
