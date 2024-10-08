from django.contrib.contenttypes.models import ContentType
from post_office.mail import send

from core.constants import MUS_STRUCTURE
from core.models import Message, Contact, FinSuiviContact
from django.conf import settings


def _send_message(recipients: list[str], copy: list[str], subject, message, instance):
    message += f"\n\n Pour voir la fiche concernée par cette notification, consultez SEVES : {settings.ROOT_URL}{instance.content_object.get_absolute_url()}"
    send(
        recipients=recipients,
        cc=copy,
        sender="no-reply@beta.gouv.fr",
        subject=f"SEVES - {subject}",
        message=message,
    )


def notify_message(instance: Message):
    recipients, copy = [], []
    message, subject = None, None
    if instance.message_type == Message.MESSAGE:
        subject = instance.title
        message = f"Bonjour,\n Vous avez reçu un message sur SEVES dont voici le contenu : \n {instance.content}"
        recipients = instance.recipients.all()
        copy = instance.recipients_copy.all()
    elif instance.message_type == Message.COMPTE_RENDU:
        subject = instance.title
        message = f"Bonjour,\n Vous avez reçu un compte rendu sur demande d'intervention sur SEVES dont voici le contenu : \n {instance.content}"
        recipients = instance.recipients.all()
    elif instance.message_type == Message.DEMANDE_INTERVENTION:
        subject = instance.title
        message = "Bonjour,\n Vous avez reçu un message sur SEVES."
        recipients = instance.recipients.structures_only()
        copy = instance.recipients_copy.structures_only()
    elif instance.message_type == Message.POINT_DE_SITUATION:
        subject = instance.title
        message = "Bonjour,\n Vous avez reçu un nouveau point de suivi sur SEVES."
        recipients = instance.content_object.contacts.agents_only()
    elif instance.message_type == Message.FIN_SUIVI:
        subject = instance.title
        message = "Bonjour,\n Vous avez reçu un nouveau point de suivi sur SEVES."
        recipients = instance.content_object.contacts.agents_only().filter(agent__structure__niveau2=MUS_STRUCTURE)
    elif instance.message_type == Message.NOTIFICATION_AC:
        subject = instance.title
        message = (
            f"Bonjour,\n une personne a déclarée la fiche {instance.content_object.numero} à l'administration centrale."
        )
        recipients = [Contact.objects.get_mus(), Contact.objects.get_bsv()]

    fiche = instance.content_object
    content_type = ContentType.objects.get_for_model(fiche)
    fin_de_suivi = FinSuiviContact.objects.filter(object_id=fiche.id, content_type=content_type).select_related(
        "contact"
    )
    contact_fin_de_suivi = [f.contact for f in fin_de_suivi]
    recipients = [r.email for r in recipients if (r.agent or (r.structure and r not in contact_fin_de_suivi))]
    copy = [c.email for c in copy if (c.agent or (c.structure and c not in contact_fin_de_suivi))]

    if recipients and message:
        _send_message(recipients, copy, subject=subject, message=message, instance=instance)
