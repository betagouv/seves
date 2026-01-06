from post_office.mail import send
from post_office.models import EmailTemplate

from core.constants import MUS_STRUCTURE
from core.models import Message, Contact, Export
from django.conf import settings


def _send_message(recipients: list[Contact], copy: list[Contact], subject: str, content: str, message_obj: Message):
    if settings.SEND_NOTIFICATIONS is False:
        return
    recipients = [r.get_email_for_object(message_obj.content_object) for r in recipients]
    recipients = [r for r in recipients if r != ""]
    copy = [c.get_email_for_object(message_obj.content_object) for c in copy]
    copy = [c for c in copy if c != ""]
    template, _ = EmailTemplate.objects.update_or_create(
        name="seves_email_template",
        defaults={
            "subject": f"{settings.EMAIL_SUBJECT_PREFIX} {message_obj.content_object.get_email_subject()} - {message_obj.get_email_type_display()} de {message_obj.sender_structure}",
            "html_content": """
                <!DOCTYPE html>
                <html>
                <div style="font-family: Arial, sans-serif;">
                    <p style="white-space: pre-wrap; line-height: 1.5; font-style: italic; margin-bottom: 20px;">Ce message concerne l’évènement : {{ evenement.get_long_email_display_name }}</p>
                    <p style="white-space: pre-wrap; line-height: 1.5; font-weight: bold; text-decoration: underline;">{{ subject }}</p>
                    <p style="white-space: pre-wrap; line-height: 1.5;">{{ content }}</p>
                    {% if documents %}
                    <p style="font-style: italic; margin-top: 20px; margin-bottom: 0px;">
                     Documents déposés sur Sèves en pièce jointe de ce message : {% for doc in documents %} {{doc.nom}} ({{ doc.get_document_type_display }}){% endfor %}
                    </p>
                    {% endif %}
                    <p style="font-weight: bold; margin-top: 20px; margin-bottom: 0px;">{{ message_obj.sender.agent.prenom }} {{ message_obj.sender.agent.nom }}</p>
                    <p style="margin-top: 0px;">{{ message_obj.sender.agent.structure }}</p>
                    <p style="margin-top: 20px;">Consulter la fiche dans Sèves : <a href="{{ fiche_url }}">{{ fiche_url }}</a></p>
                    <p>Merci de ne pas répondre directement à ce message.</p>
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
            "documents": message_obj.documents.all(),
            "evenement": message_obj.content_object,
            "fiche_url": f"{settings.ROOT_URL}{message_obj.content_object.get_absolute_url()}",
        },
    )


def _filter_contacts_in_fin_de_suivi(recipients, object):
    emails_to_exclude = Contact.objects.get_emails_in_fin_de_suivi_for_object(object)

    return [r for r in recipients if r not in emails_to_exclude]


def send_as_seves(
    *, recipients: list[Contact], subject, message, html_message, object, link_to_fiche=True, filter_fin_suivi=True
):
    if settings.SEND_NOTIFICATIONS is False:
        return
    recipients = [r.get_email_for_object(object) for r in recipients]
    recipients = [r for r in recipients if r != ""]
    if filter_fin_suivi:
        recipients = _filter_contacts_in_fin_de_suivi(recipients, object)
    if link_to_fiche:
        suffix_html = f"""<p>
            Consulter la fiche dans Sèves : <a href="{settings.ROOT_URL}{object.get_absolute_url()}">{settings.ROOT_URL}{object.get_absolute_url()}</a>.
            <br>Merci de ne pas répondre directement à ce message.</p>"""
        suffix = f"""Consulter la fiche dans Sèves : {settings.ROOT_URL}{object.get_absolute_url()}
        Merci de ne pas répondre directement à ce message."""
    else:
        suffix_html = "<p>Merci de ne pas répondre directement à ce message.</p>"
        suffix = "Merci de ne pas répondre directement à ce message."

    html = f"""<!DOCTYPE html>
        <html>
        <div style="font-family: Arial, sans-serif;">
            {html_message}
            {suffix_html}
        </div>
        </html>
        """

    message = f"""
        {message}

        {suffix}
    """

    send(
        recipients=recipients,
        subject=f"{settings.EMAIL_SUBJECT_PREFIX} {subject}",
        html_message=html,
        message=message,
    )


def notify_message(message_obj: Message):
    if message_obj.is_draft:
        return
    recipients, copy = [], []
    content = message_obj.content

    match message_obj.message_type:
        case Message.MESSAGE:
            recipients = message_obj.recipients.all()
            copy = message_obj.recipients_copy.all()
        case Message.COMPTE_RENDU | Message.POINT_DE_SITUATION:
            recipients = message_obj.recipients.all()
        case Message.DEMANDE_INTERVENTION:
            recipients = message_obj.recipients.structures_only()
            copy = message_obj.recipients_copy.structures_only()
        case Message.NOTIFICATION_AC:
            content = f"Bonjour,\nLa fiche {message_obj.content_object.numero} vient d'être déclarée à l'administration centrale."
            recipients = [Contact.objects.get_mus(), Contact.objects.get_bsv()]

    if recipients and content:
        _send_message(
            recipients,
            copy,
            subject=message_obj.title,
            content=content,
            message_obj=message_obj,
        )


def notify_contact_agent_added_or_removed(contact: Contact, obj, added, user):
    users_structure = user.agent.structure
    if added is False:
        if contact.structure == users_structure or (contact.agent and contact.agent.structure == users_structure):
            return  # Never send the notification if the removal is performed by a user inside the same structure

    action = "ajouté au" if added else "retiré du"
    subject = "Ajout aux contacts" if added else "Retrait des contacts"
    by_text = "" if added else f" par {user.agent.agent_with_structure}"
    send_as_seves(
        object=obj,
        recipients=[contact],
        subject=f"{obj.get_short_email_display_name()} - {subject}",
        message=f"""
Bonjour,
Vous avez été {action} suivi de l’évènement : {obj.get_long_email_display_name()}{by_text}
        """,
        html_message=f"""
    <p>Bonjour,<br>
    Vous avez été {action} suivi de l’évènement : {obj.get_long_email_display_name_as_html()}{by_text}.</p>
    """,
    )


def notify_export_is_ready(export: Export, object):
    send_as_seves(
        recipients=[export.user.agent.contact_set.get()],
        object=object,
        subject="Votre export est prêt",
        message=f"""
Bonjour,

L'export CSV que vous avez demandé est prêt, le lien pour télécharger le fichier est : {export.file.url} .

Attention, le lien n'est valable que durant 1 heure.

Si vous rencontrez des difficultés, vous pouvez consulter notre centre d’aide ou nous en faire part à l’adresse email support@seves.beta.gouv.fr.
        """,
        html_message=f"""
    <p>Bonjour,<br>
    L'export CSV que vous avez demandé est prêt, le lien pour télécharger le fichier est&nbsp;: <a href="{export.file.url}">{export.file.url}</a>.</p>
    <p>Attention, le lien n'est valable que durant 1 heure.</p>
    <p>Si vous rencontrez des difficultés, vous pouvez consulter notre centre d’aide ou nous en faire part à l’adresse email <a href="mailto:support@seves.beta.gouv.fr">support@seves.beta.gouv.fr</a>.</p>
        """,
        link_to_fiche=False,
        filter_fin_suivi=False,
    )


def notify_fin_de_suivi(object, structure):
    send_as_seves(
        recipients=object.contacts.agents_only().filter(agent__structure__niveau2=MUS_STRUCTURE),
        object=object,
        subject=f"{object.get_short_email_display_name()} - Fin de suivi",
        message=f"""
    Bonjour,

    La fin de suivi a été déclarée pour {structure} sur l’évènement : {object.get_long_email_display_name()}
            """,
        html_message=f"""
        <p>Bonjour,</p>
        <p>La fin de suivi a été déclarée pour {structure} sur l’évènement : {object.get_long_email_display_name_as_html()}</p>
            """,
    )


def notify_message_deleted(message: Message):
    if message.is_draft:
        return
    object = message.content_object
    recipients = list(message.recipients.all())
    copy = list(message.recipients_copy.all())
    recipients_structure = list(message.recipients.structures_only())
    copy_structures = list(message.recipients_copy.structures_only())
    send_as_seves(
        recipients=list(set(recipients + copy + recipients_structure + copy_structures)),
        object=object,
        subject=f"{object.get_short_email_display_name()} - Suppression d’un élément du fil de suivi",
        message=f"""
    Bonjour,

    Un élément du fil de suivi de l’évènement : {object.get_long_email_display_name()} a été supprimé.

    {message.get_message_type_display()} - {message.title}
            """,
        html_message=f"""
        <p>Bonjour,<br>
        Un élément du fil de suivi de l’évènement {object.get_long_email_display_name_as_html()} a été supprimé. </p>
        <p>{message.get_message_type_display()} - {message.title}</p>
            """,
    )


def notify_object_cloture(object):
    send_as_seves(
        recipients=object.contacts.structures_only().exclude_mus(),
        object=object,
        subject=f" {object.get_short_email_display_name()} - Clôture de l’évènement",
        message=f"""
        Bonjour,
        L’évènement {object.get_short_email_display_name()} a été clôturé. Les informations restent néanmoins consultables.

        {object.get_email_cloture_text() if hasattr(object, "get_email_cloture_text") else ""}
            """,
        html_message=f"""
        <p>Bonjour,<br>
        L’évènement <b>{object.get_short_email_display_name()}</b> a été clôturé. Les informations restent néanmoins consultables. </p>

        {"<p>" + object.get_email_cloture_text_html() + "</p>" if hasattr(object, "get_email_cloture_text_html") else ""}
        """,
    )
