from post_office.mail import send
from post_office.models import EmailTemplate

from core.constants import MUS_STRUCTURE
from core.models import Message, Contact, Export
from django.conf import settings


def _send_message(recipients: list[str], copy: list[str], subject: str, content: str, message_obj: Message):
    template, _ = EmailTemplate.objects.update_or_create(
        name="seves_email_template",
        defaults={
            "subject": f"{settings.EMAIL_SUBJECT_PREFIX} {message_obj.content_object.get_email_subject()} - {message_obj.get_email_type_display()}",
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
        sender="no-reply@seves.beta.gouv.fr",
        template=template,
        context={
            "message_obj": message_obj,
            "subject": subject,
            "content": content,
            "fiche_url": f"{settings.ROOT_URL}{message_obj.content_object.get_absolute_url_with_message(message_obj.id)}",
        },
    )


def notify_message(message_obj: Message):
    if message_obj.is_draft:
        return
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
        case Message.NOTIFICATION_AC:
            content = f"Bonjour,\nLa fiche {message_obj.content_object.numero} vient d'être déclarée à l'administration centrale."
            recipients = [Contact.objects.get_mus().email, Contact.objects.get_bsv().email]

    if recipients and content:
        _send_message(recipients, copy, subject=message_obj.title, content=content, message_obj=message_obj)


def get_notify_contact_agent_email_subject(obj):
    subject = f"[Sèves {obj._meta.app_label.upper()}] "
    if hasattr(obj, "organisme_nuisible"):
        subject += f"{obj.organisme_nuisible.code_oepp} "
    subject += f"{obj.numero}"
    return subject


def notify_contact_agent(contact_agent: Contact, obj):
    send(
        recipients=f"{contact_agent.agent.prenom} {contact_agent.agent.nom} <{contact_agent.email}>",
        subject=get_notify_contact_agent_email_subject(obj),
        message=f"""
Ajout en contact d’une fiche
Bonjour,
Vous avez été ajouté en contact de la fiche n° {obj.numero}.
Vous pouvez y accéder avec le lien suivant : https://seves.beta.gouv.fr/{obj.get_absolute_url()}
        """,
        html_message=f"""
<!DOCTYPE html>
<html>
<div style="font-family: Arial, sans-serif;">
    <p style="font-weight: bold;">Ajout en contact d’une fiche</p>
    <p>Bonjour,</p>
    <p>Vous avez été ajouté en contact de la fiche n° {obj.numero}.</p>
    <p>Vous pouvez y accéder avec le lien suivant : <a href="https://seves.beta.gouv.fr{obj.get_absolute_url()}">https://seves.beta.gouv.fr{obj.get_absolute_url()}</a></p>
</div>
</html>
        """,
    )


def notify_export_is_ready(export: Export):
    send(
        recipients=[export.user.email],
        subject="Sèves - Votre export est prêt",
        message=f"""
Bonjour,

L'export CSV que vous avez demandé est prêt, le lien pour télécharger le fichier est : {export.file.url} .

Attention, le lien n'est valable que durant 1 heure.
Si vous rencontrez des difficultés, vous pouvez consulter notre centre d’aide ou nous en faire part à l’adresse email support@seves.beta.gouv.fr.
Merci de ne pas répondre directement à ce message.
Cordialement,
L’équipe Sèves

        """,
        html_message=f"""
<!DOCTYPE html>
<html>
<div style="font-family: Arial, sans-serif;">
    <p>Bonjour,</p>
    <p>L'export CSV que vous avez demandé est prêt, le lien pour télécharger le fichier est&nbsp;: <a href="{export.file.url}">{export.file.url}</a>.</p>
    <p>Attention, le lien n'est valable que durant 1 heure.</p>
    <p>Si vous rencontrez des difficultés, vous pouvez consulter notre centre d’aide ou nous en faire part à l’adresse email <a href="mailto:support@seves.beta.gouv.fr">support@seves.beta.gouv.fr</a>.
Merci de ne pas répondre directement à ce message. </p>
</div>
</html>
        """,
    )


def _add_footer(object):
    return f"""
    Consulter la fiche dans Sèves : {settings.ROOT_URL}{object.get_absolute_url()}
    Merci de ne pas répondre directement à ce message.
    """


def _add_footer_html(object):
    return f"""
    <p>Consulter la fiche dans Sèves : <a href="{settings.ROOT_URL}{object.get_absolute_url()}">{settings.ROOT_URL}{object.get_absolute_url()}</a></p>
    <p>Merci de ne pas répondre directement à ce message.</p>
    """


def notify_fin_de_suivi(object, structure):
    recipients = [r.email for r in object.contacts.agents_only().filter(agent__structure__niveau2=MUS_STRUCTURE)]
    send(
        recipients=recipients,
        subject=f"{settings.EMAIL_SUBJECT_PREFIX} {object.get_short_email_display_name()} - Fin de suivi",
        message=f"""
    Bonjour,

    La fin de suivi a été déclarée pour {structure} sur l’évènement : {object.get_long_email_display_name()}

    {_add_footer(object)}
            """,
        html_message=f"""
    <!DOCTYPE html>
    <html>
    <div style="font-family: Arial, sans-serif;">
        <p>Bonjour,</p>
        <p>La fin de suivi a été déclarée pour {structure} sur l’évènement : {object.get_long_email_display_name()}</p>
        {_add_footer_html(object)}
    </div>
    </html>
            """,
    )
