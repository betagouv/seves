from django.conf import settings
from django.core.management import call_command
import pytest

from core.factories import ContactAgentFactory, DocumentFactory
from core.models import Document
from ssa.factories import EvenementProduitFactory, InvestigationCasHumainFactory


@pytest.mark.django_db
def test_send_email_document_uploaded(mailoutbox, mus_contact):
    contact_agent = ContactAgentFactory(
        with_active_agent__with_groups=(settings.SSA_GROUP,), agent__structure=mus_contact.structure
    )
    evenement_produit = EvenementProduitFactory()
    evenement_produit.contacts.add(contact_agent)
    doc_1 = DocumentFactory(content_object=evenement_produit, document_type=Document.TypeDocument.RAPPORT_ANALYSE)
    doc_2 = DocumentFactory(content_object=evenement_produit, document_type=Document.TypeDocument.ANALYSE_RISQUE)
    doc_3 = DocumentFactory(content_object=evenement_produit, document_type=Document.TypeDocument.SIGNALEMENT_AUTRE)
    evenement_produit.documents.add(doc_1, doc_2, doc_3)

    investigation = InvestigationCasHumainFactory()
    investigation.contacts.add(contact_agent)
    doc_4 = DocumentFactory(content_object=investigation, document_type=Document.TypeDocument.RAPPORT_ANALYSE)
    doc_5 = DocumentFactory(content_object=investigation, document_type=Document.TypeDocument.ANALYSE_RISQUE)
    doc_6 = DocumentFactory(content_object=investigation, document_type=Document.TypeDocument.SIGNALEMENT_AUTRE)
    investigation.documents.add(doc_4, doc_5, doc_6)

    # This type of document alone should not trigger an email
    evenement_produit_not_triggered = EvenementProduitFactory()
    evenement_produit_not_triggered.contacts.add(contact_agent)
    doc_7 = DocumentFactory(
        content_object=evenement_produit_not_triggered, document_type=Document.TypeDocument.SIGNALEMENT_AUTRE
    )
    evenement_produit_not_triggered.documents.add(doc_7)

    call_command("send_document_emails_batch")
    assert len(mailoutbox) == 2

    mail = mailoutbox[0]
    assert "Ajout de document" in mail.subject
    assert doc_1.nom in mail.body
    assert doc_2.nom in mail.body
    assert doc_3.nom not in mail.body

    mail = mailoutbox[1]
    assert "Ajout de document" in mail.subject
    assert doc_4.nom in mail.body
    assert doc_5.nom in mail.body
    assert doc_6.nom not in mail.body

    # Make sure the emails are sent only once
    call_command("send_document_emails_batch")
    assert len(mailoutbox) == 2
