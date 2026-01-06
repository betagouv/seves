from core.models import Contact
from core.notifications import send_as_seves
from tiac.models import EvenementSimple, InvestigationTiac


def notify_transfer(evenement: EvenementSimple):
    send_as_seves(
        recipients=[evenement.transfered_to.contact_set.get()],
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
        recipients=[Contact.objects.get_mus()],
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


def notify_investigation_coordonnee(object: InvestigationTiac, user):
    send_as_seves(
        recipients=[user.agent.contact_set.get(), Contact.objects.get_mus()],
        object=object,
        subject=f"{object.get_short_email_display_name()} - Investigation coordonnée",
        message=f"""
        Bonjour,
        L'agent {user.agent.agent_with_structure} a édité l’évènement suivant {object.get_long_email_display_name()} en “Investigation coordonnée / MUS informée”.

        Si ce n’est pas déjà fait, pensez à informer la MUS et/ ou les autres DDPP concernées des raisons de ce choix.
            """,
        html_message=f"""
        <p>Bonjour,<br>
        L'agent {user.agent.agent_with_structure} a édité l’évènement suivant {object.get_long_email_display_name_as_html()} en “Investigation coordonnée / MUS informée”. </p>

        <p>Si ce n’est pas déjà fait, pensez à informer la MUS et/ ou les autres DDPP concernées des raisons de ce choix </p>
        """,
    )


def notify_conclusion(object: InvestigationTiac, user):
    send_as_seves(
        recipients=object.contacts.agents_only().exclude(id=user.agent.contact_set.get().id),
        object=object,
        subject=f"{object.get_short_email_display_name()} - Conclusion suspicion TIAC",
        message=f"""
        Bonjour,
        La conclusion de la suspicion de TIAC a été modifiée vers « {object.get_suspicion_conclusion_display() or "Vide"} » pour l’évènement : {object.get_long_email_display_name()}
        """,
        html_message=f"""
        <p>Bonjour,<br>
        La conclusion de la suspicion de TIAC a été modifiée vers « {object.get_suspicion_conclusion_display() or "Vide"} » pour l’évènement : {object.get_long_email_display_name_as_html()}</p>
        """,
    )
