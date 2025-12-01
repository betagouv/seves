from django.conf import settings

from core.models import Contact
from core.notifications import _add_footer, _add_footer_html
from ssa.models import EvenementProduit
from post_office.mail import send


def notify_type_evenement_fna(evenement: EvenementProduit, user):
    recipients = [Contact.objects.get_mus().email, user.agent.contact_set.get().email]
    send(
        recipients=recipients,
        subject=f"{settings.EMAIL_SUBJECT_PREFIX} {evenement.get_short_email_display_name()} - Modification type d’évènement",
        message=f"""
    Bonjour,

    L'agent {user.agent.agent_with_structure} a modifié l’évènement suivant {evenement.numero} {evenement.get_long_email_display_name_suffix()} en “Alerte produit nationale”.

    Si ce n’est pas déja fait, pensez à informer la MUS et/ ou les autres DDPP concernées des raisons de ce changement.

    {_add_footer(evenement)}
            """,
        html_message=f"""
    <!DOCTYPE html>
    <html>
    <div style="font-family: Arial, sans-serif;">
        <p>Bonjour,<br>
            L'agent {user.agent.agent_with_structure} a modifié l’évènement suivant <b>{evenement.numero}</b> {evenement.get_long_email_display_name_suffix()} en “Alerte produit nationale”. </p>
        <p>Si ce n’est pas déja fait, pensez à informer la MUS et/ ou les autres DDPP concernées des raisons de ce changement. </p>
        {_add_footer_html(evenement)}
    </div>
    </html>
            """,
    )


def notify_souches_clusters(evenement: EvenementProduit, user):
    recipients = [c.email for c in evenement.contacts.agents_only().exclude(id=user.agent.contact_set.get().id)]
    send(
        recipients=recipients,
        subject=f"{settings.EMAIL_SUBJECT_PREFIX} {evenement.get_long_email_display_name()} - Souche / cluster",
        message=f"""
    Bonjour,
    Les champs “souche” et / ou “cluster” ont été modifiés pour l’évènement : {evenement.get_long_email_display_name()}
    - Référence souche : {evenement.reference_souches or "Vide"}
    - Référence cluster : {evenement.reference_clusters or "Vide"}

    {_add_footer(evenement)}
            """,
        html_message=f"""
    <!DOCTYPE html>
    <html>
    <div style="font-family: Arial, sans-serif;">
        <p>Bonjour,<br>
        Les champs “souche” et / ou “cluster” ont été modifiés pour l’évènement : {evenement.get_long_email_display_name_as_html()}.
        <ul>
        <li>- Référence souche : {evenement.reference_souches or "Vide"}</li>
        <li>- Référence cluster : {evenement.reference_clusters or "Vide"}</li>
        </ul>
        </p>
        {_add_footer_html(evenement)}
    </div>
    </html>
            """,
    )


def notify_alimentation_animale(evenement: EvenementProduit):
    recipients = [c.email for c in evenement.contacts.structures_only()]
    send(
        recipients=recipients,
        subject=f"{settings.EMAIL_SUBJECT_PREFIX} {evenement.get_long_email_display_name()} - Inclut des aliments pour animaux",
        message=f"""
    Bonjour,
    L’évènement suivant {evenement.get_long_email_display_name()} inclut désormais des aliments pour animaux.

    {_add_footer(evenement)}
            """,
        html_message=f"""
    <!DOCTYPE html>
    <html>
    <div style="font-family: Arial, sans-serif;">
        <p>Bonjour,<br>
        L’évènement suivant {evenement.get_long_email_display_name_as_html()} inclut désormais des aliments pour animaux.
        </p>
        {_add_footer_html(evenement)}
    </div>
    </html>
            """,
    )
