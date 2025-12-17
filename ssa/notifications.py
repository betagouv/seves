from core.models import Contact
from core.notifications import send_as_seves
from ssa.models import EvenementProduit


def notify_type_evenement_fna(evenement: EvenementProduit, user):
    recipients = [Contact.objects.get_mus(), user.agent.contact_set.get()]
    send_as_seves(
        recipients=recipients,
        object=evenement,
        subject=f"{evenement.get_short_email_display_name()} - Modification type d’évènement",
        message=f"""
    Bonjour,

    L'agent {user.agent.agent_with_structure} a modifié l’évènement suivant {evenement.numero} {evenement.get_long_email_display_name_suffix()} en “Alerte produit nationale”.

    Si ce n’est pas déja fait, pensez à informer la MUS et/ ou les autres DDPP concernées des raisons de ce changement.
            """,
        html_message=f"""
        <p>Bonjour,<br>
            L'agent {user.agent.agent_with_structure} a modifié l’évènement suivant <b>{evenement.numero}</b> {evenement.get_long_email_display_name_suffix()} en “Alerte produit nationale”. </p>
        <p>Si ce n’est pas déja fait, pensez à informer la MUS et/ ou les autres DDPP concernées des raisons de ce changement. </p>
            """,
    )


def notify_souches_clusters(evenement: EvenementProduit, user):
    send_as_seves(
        recipients=evenement.contacts.agents_only().exclude(id=user.agent.contact_set.get().id),
        object=evenement,
        subject=f"{evenement.get_short_email_display_name()} - Souche / cluster",
        message=f"""
    Bonjour,
    Les champs “souche” et / ou “cluster” ont été modifiés pour l’évènement : {evenement.get_long_email_display_name()}
    - Référence souche : {evenement.reference_souches or "Vide"}
    - Référence cluster : {evenement.reference_clusters or "Vide"}
            """,
        html_message=f"""
        <p>Bonjour,<br>
        Les champs “souche” et / ou “cluster” ont été modifiés pour l’évènement : {evenement.get_long_email_display_name_as_html()}.
        <ul>
        <li>- Référence souche : {evenement.reference_souches or "Vide"}</li>
        <li>- Référence cluster : {evenement.reference_clusters or "Vide"}</li>
        </ul>
        </p>
            """,
    )


def notify_alimentation_animale(evenement: EvenementProduit):
    send_as_seves(
        recipients=evenement.contacts.structures_only(),
        object=evenement,
        subject=f"{evenement.get_short_email_display_name()} - Inclut des aliments pour animaux",
        message=f"""
    Bonjour,
    L’évènement suivant {evenement.get_long_email_display_name()} inclut désormais des aliments pour animaux.
            """,
        html_message=f"""
        <p>Bonjour,<br>
        L’évènement suivant {evenement.get_long_email_display_name_as_html()} inclut désormais des aliments pour animaux.
        </p>
            """,
    )
