from post_office.mail import send

from core.constants import MUS_STRUCTURE
from core.models import Message, Contact


def _send_message(recipients: list[str], copy: list[str], subject, message):
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
        recipients = [r.email for r in instance.recipients.all()]
        copy = [r.email for r in instance.recipients_copy.all()]
    elif instance.message_type == Message.COMPTE_RENDU:
        subject = instance.title
        message = f"Bonjour,\n Vous avez reçu un compte rendu sur demande d'intervention sur SEVES dont voici le contenu : \n {instance.content}"
        recipients = [r.email for r in instance.recipients.all()]
    elif instance.message_type == Message.DEMANDE_INTERVENTION:
        subject = instance.title
        message = "Bonjour,\n Vous avez reçu un message sur SEVES."
        recipients = [r.email for r in instance.recipients.structures_only()]
        copy = [r.email for r in instance.recipients_copy.structures_only()]
    elif instance.message_type == Message.POINT_DE_SITUATION:
        subject = instance.title
        message = "Bonjour,\n Vous avez reçu un nouveau point de suivi sur SEVES."
        recipients = [c.email for c in instance.content_object.contacts.agents_only()]
    elif instance.message_type == Message.FIN_SUIVI:
        subject = instance.title
        message = "Bonjour,\n Vous avez reçu un nouveau point de suivi sur SEVES."
        recipients = instance.content_object.contacts.agents_only().filter(agent__structure__niveau2=MUS_STRUCTURE)
        recipients = [r.email for r in recipients]
    elif instance.message_type == Message.NOTIFICATION_AC:
        subject = instance.title
        message = (
            f"Bonjour,\n une personne a déclarée la fiche {instance.content_object.numero} à l'administration centrale."
        )
        recipients = [Contact.objects.get_mus().email, Contact.objects.get_bsv().email]

    if recipients and message:
        _send_message(recipients, copy, subject=subject, message=message)
