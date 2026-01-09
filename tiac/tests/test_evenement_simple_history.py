from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from playwright.sync_api import expect

from core.factories import MessageFactory
from core.models import LienLibre
from tiac.factories import EvenementSimpleFactory
from tiac.models import EvenementSimple
from tiac.tests.pages import EvenementSimpleDetailsPage


def test_can_view_evenement_simple_history(live_server, page, mus_contact):
    evenement = EvenementSimpleFactory()

    message = MessageFactory(content_object=evenement)
    message.is_deleted = True
    message.save()

    details_page = EvenementSimpleDetailsPage(page, live_server.url)
    details_page.navigate(evenement)
    details_page.transform()

    other_evenement = EvenementSimpleFactory()
    lien = LienLibre.objects.create(related_object_1=other_evenement, related_object_2=evenement)
    lien.delete()

    content_type = ContentType.objects.get_for_model(EvenementSimple)
    url = reverse("revision-list", kwargs={"content_type": content_type.pk, "pk": evenement.pk})
    page.goto(f"{live_server.url}{url}")

    expect(page.locator("tr")).to_have_count(
        len(
            [
                "One for table header",
                "One (fake) line for the creation of the object",
                "One for the deletion of the message",
                "One for the change of state to Cloturé (due to transformation into Investigation)",
                "One for the LienLibre that was added (due to transformation into Investigation)",
                "One for the note for the transformation (due to transformation into Investigation)",
                "One for creation of the LienLibre",
                "One for deletion of the LienLibre",
            ]
        )
    )

    expect(page.get_by_text(f"Le lien '{str(other_evenement)}' a été ajouté à la fiche", exact=True)).to_be_visible()
    expect(page.get_by_text(f"Le lien '{str(other_evenement)}' a été supprimé à la fiche", exact=True)).to_be_visible()
    expect(page.get_by_text("Structure Test")).to_have_count(
        len(["Cloturé for transformation", "Lien libre for transformation", "Note for transformation"])
    )
