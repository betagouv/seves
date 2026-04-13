from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from playwright.sync_api import Page, expect

from core.factories import ContactAgentFactory, ContactStructureFactory, DocumentFactory, MessageFactory
from core.models import Message


def generic_test_bloc_commun_nb_items(live_server, page: Page, target_object, other_obj):
    MessageFactory(status=Message.Status.AVANT_SAUVEGARDE, content_object=other_obj)
    MessageFactory(status=Message.Status.BROUILLON, content_object=other_obj)
    MessageFactory(status=Message.Status.FINALISE, content_object=other_obj)

    MessageFactory(status=Message.Status.AVANT_SAUVEGARDE, content_object=target_object)
    MessageFactory(status=Message.Status.BROUILLON, content_object=target_object)
    MessageFactory(status=Message.Status.FINALISE, content_object=target_object)

    ContactStructureFactory()
    ContactAgentFactory()
    target_object.contacts.add(ContactStructureFactory())
    target_object.contacts.add(ContactAgentFactory())

    DocumentFactory(content_object=other_obj, is_infected=False)
    DocumentFactory(content_object=other_obj, is_infected=False)
    DocumentFactory(content_object=target_object, is_infected=False)
    DocumentFactory(content_object=target_object, is_deleted=True, is_infected=False)

    page.goto(f"{live_server.url}{target_object.get_absolute_url()}")
    expect(page.locator("#tabpanel-messages")).to_contain_text("Fil de suivi (1)")
    expect(page.locator("#tabpanel-contacts")).to_contain_text("Contacts (2)")
    expect(page.locator("#tabpanel-documents")).to_contain_text("Documents (1)")


def generic_test_can_preview_image_from_bloc_commun(live_server, page: Page, target_object):
    path = settings.BASE_DIR / "static/images/marianne.png"
    file = SimpleUploadedFile(
        name="test.png",
        content=path.read_bytes(),
        content_type="image/png",
    )
    DocumentFactory(content_object=target_object, is_infected=False, file=file)

    page.goto(f"{live_server.url}{target_object.get_absolute_url()}")
    page.locator("#tabpanel-documents").click()
    page.locator(".fr-icon-eye-line").click()
    img = page.locator('img[src*="_test.png"]')
    expect(img).to_be_visible()
