from post_office.mail import send
from post_office.models import EmailTemplate

from core.constants import MUS_STRUCTURE
from core.models import Message, Contact
from django.conf import settings


def _send_message(recipients: list[str], copy: list[str], subject: str, content: str, message_obj: Message):
    template, _ = EmailTemplate.objects.update_or_create(
        name="seves_email_template",
        defaults={
            "subject": f"[Sèves] {message_obj.content_object.get_email_subject()} - {message_obj.get_email_type_display()}",
            "html_content": """
                <!DOCTYPE html>
                <html>
                <div style="font-family: Arial, sans-serif;">
                    <p style="white-space: pre-wrap; line-height: 1.5; font-weight: bold; text-decoration: underline;">{{ subject }}</p>
                    <p style="white-space: pre-wrap; line-height: 1.5;">{{ content }}</p>
                    <p style="font-weight: bold; margin-top: 20px; margin-bottom: 0px;">{{ message_obj.sender.agent.prenom }} {{ message_obj.sender.agent.nom }}</p>
                    <p style="margin-top: 0px;">{{ message_obj.sender.agent.structure }}</p>
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
            "message_obj": message_obj,
            "subject": subject,
            "content": content,
            "fiche_url": f"{settings.ROOT_URL}{message_obj.content_object.get_absolute_url_with_message(message_obj.id)}",
        },
    )


def notify_message(message_obj: Message):
    recipients, copy = [], []
    content = message_obj.content

    match message_obj.message_type:
        case Message.MESSAGE:
            recipients = [r.email for r in message_obj.recipients.all()]
            copy = [r.email for r in message_obj.recipients_copy.all()]
        case Message.COMPTE_RENDU | Message.POINT_DE_SITUATION:
            recipients = [r.email for r in message_obj.recipients.all()]
        case Message.DEMANDE_INTERVENTION:
            recipients = [r.email for r in message_obj.recipients.structures_only()]
            copy = [r.email for r in message_obj.recipients_copy.structures_only()]
        case Message.FIN_SUIVI:
            recipients = message_obj.content_object.contacts.agents_only().filter(
                agent__structure__niveau2=MUS_STRUCTURE
            )
            recipients = [r.email for r in recipients]
        case Message.NOTIFICATION_AC:
            content = f"Bonjour,\nLa fiche {message_obj.content_object.numero} vient d'être déclarée à l'administration centrale."
            recipients = [Contact.objects.get_mus().email, Contact.objects.get_bsv().email]

    if recipients and content:
        _send_message(recipients, copy, subject=message_obj.title, content=content, message_obj=message_obj)
