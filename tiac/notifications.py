from core.models import Contact
from core.notifications import send_as_seves
from tiac.models import EvenementSimple, InvestigationTiac


def notify_transfer(evenement: EvenementSimple):
    recipients = [evenement.transfered_to.contact_set.get().email]
    send_as_seves(
        recipients=recipients,
        object=evenement,
        subject=f"{evenement.get_short_email_display_name()} - Transfert de l’évènement",
        message=f"""
    Bonjour,

    L’évènement {evenement.get_short_email_display_name()} a été transféré à votre structure
    - en provenance de : {evenement.createur}
            """,
        html_message=f"""
        <p>Bonjour,<br>
            L’évènement {evenement.get_long_email_display_name_as_html()} a été transféré à votre structure<br>
            <ul>
            <li>en provenance de : {evenement.createur}</li>
            </ul>
            </p>
            """,
    )


def notify_transformation(old: EvenementSimple, new: InvestigationTiac):
    send_as_seves(
        recipients=[Contact.objects.get_mus().email],
        object=new,
        subject=f"{new.get_short_email_display_name()} - Passage en investigation TIAC",
        message=f"""
        Bonjour,

        L’évènement {old.numero} de type “Enregistrement simple“ a été passé en “Investigation de TIAC”. Le nouvel évènement est le suivant : {new.numero}
            """,
        html_message=f"""
        <p>Bonjour,<br>
            L’évènement <b>{old.numero}</b> de type “Enregistrement simple” a été passé en “Investigation de TIAC”. Le nouvel évènement est le suivant : <b>{new.numero}</b>
            </p>
            """,
    )
