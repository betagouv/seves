from post_office.mail import send
from post_office.models import EmailTemplate

from core.constants import MUS_STRUCTURE
from core.models import Message, Contact
from django.conf import settings


def _send_message(recipients: list[str], copy: list[str], subject, message, instance):
    template, _ = EmailTemplate.objects.update_or_create(
        name="seves_email_template",
        defaults={
            "subject": f"Sèves - {instance.content_object.numero} - {instance.message_type} - {subject}",
            "html_content": """
                <!DOCTYPE html>
                <html>
                <div style="font-family: Arial, sans-serif;">
                    <p style="white-space: pre-wrap; line-height: 1.5;">{{ message }}</p>
                    <p style="font-weight: bold; margin-top: 20px; margin-bottom: 0px;">{{ instance.sender.agent.prenom }} {{ instance.sender.agent.nom }}</p>
                    <p style="margin-top: 0px;">{{ instance.sender.agent.structure }}</p>
                    <p style="margin-top: 20px;">Consulter la fiche dans Sèves : <a href="{{ fiche_url }}">{{ fiche_url }}</a></p>
                </div>
                </html>
            """,
        },
    )
    send(
        recipients=recipients,
        cc=copy,
        sender="no-reply@beta.gouv.fr",
        template=template,
        context={
            "subject": subject,
            "instance": instance,
            "message": message,
            "fiche_url": f"{settings.ROOT_URL}{instance.content_object.get_absolute_url()}",
        },
    )


def notify_message(instance: Message):
    recipients, copy = [], []
    message = instance.content

    match instance.message_type:
        case Message.MESSAGE:
            recipients = [r.email for r in instance.recipients.all()]
            copy = [r.email for r in instance.recipients_copy.all()]
        case Message.COMPTE_RENDU:
            recipients = [r.email for r in instance.recipients.all()]
        case Message.DEMANDE_INTERVENTION:
            recipients = [r.email for r in instance.recipients.structures_only()]
            copy = [r.email for r in instance.recipients_copy.structures_only()]
        case Message.POINT_DE_SITUATION:
            recipients = [c.email for c in instance.content_object.contacts.agents_only()]
        case Message.FIN_SUIVI:
            recipients = instance.content_object.contacts.agents_only().filter(agent__structure__niveau2=MUS_STRUCTURE)
            recipients = [r.email for r in recipients]
        case Message.NOTIFICATION_AC:
            message = f"Bonjour,\nLa fiche {instance.content_object.numero} vient d'être déclarée à l'administration centrale."
            recipients = [Contact.objects.get_mus().email, Contact.objects.get_bsv().email]

    if recipients and message:
        _send_message(recipients, copy, subject=instance.title, message=message, instance=instance)
