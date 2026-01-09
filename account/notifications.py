from post_office.mail import send

from core.constants import SV_DOMAIN, SSA_DOMAIN
from core.models import Contact


def format_groups_for_email(groups: list[str]) -> str:
    match groups:
        case ["SV"]:
            return SV_DOMAIN
        case ["SSA"]:
            return SSA_DOMAIN
        case ["SV", "SSA"]:
            return f"{SV_DOMAIN} et {SSA_DOMAIN}"
        case _:
            return ""


def notify_new_permission(contact_agent: Contact, active_groups: list[str]):
    full_group_name = format_groups_for_email(active_groups)
    send(
        recipients=f"{contact_agent.agent.prenom} {contact_agent.agent.nom} <{contact_agent.email}>",
        subject=f"[Sèves {'/'.join(active_groups)}] - Droits d'accès",
        message=f"""
    Droits d’accès Sèves
    Bonjour,
    Les droits d’accès vous ont été attribués pour Sèves {full_group_name}.
    Vous pouvez désormais accéder à Sèves au lien suivant : https://seves.beta.gouv.fr
        """,
        html_message=f"""
    <!DOCTYPE html>
    <html>
    <div style="font-family: Arial, sans-serif;">
        <p style="font-weight: bold;">Droits d’accès Sèves</p>
        <p>Bonjour,</p>
        <p>Les droits d’accès vous ont été attribués pour Sèves {full_group_name}.</p>
        <p>Vous pouvez désormais accéder à Sèves au lien suivant : <a href="https://seves.beta.gouv.fr">Sèves</a></p>
    </div>
    </html>
        """,
    )


def notify_new_admin_permission(contact_agent: Contact, active_groups: list[str]):
    full_group_name = format_groups_for_email(active_groups)
    send(
        recipients=f"{contact_agent.agent.prenom} {contact_agent.agent.nom} <{contact_agent.email}>",
        subject=f"[Sèves {'/'.join(active_groups)}] - Rôle d’administrateur",
        message=f"""
    Rôle d’administrateur Sèves
    Bonjour,
    Le rôle d’administrateur vous a été attribué pour Sèves {full_group_name}. Vous pouvez désormais donner les droits d’accès à Sèves pour les agents de votre structure depuis la page de gestion des droits d’accès (https://seves.beta.gouv.fr/account/permissions/)

    Si vous rencontrez des difficultés, vous pouvez consulter notre centre d’aide ou nous en faire part à l’adresse email support@seves.beta.gouv.fr.
    Merci de ne pas répondre directement à ce message.
        """,
        html_message=f"""
    <!DOCTYPE html>
    <html>
    <div style="font-family: Arial, sans-serif;">
        <p style="font-weight: bold;">Rôle d’administrateur Sèves</p>
        <p>Bonjour,</p>
        <p>Le rôle d’administrateur vous a été attribué pour Sèves {full_group_name}.
        Vous pouvez désormais donner les droits d’accès à Sèves pour les agents de votre structure depuis la page de <a href="https://seves.beta.gouv.fr/account/permissions/">gestion des droits d’accès</a>.</p>
        <p>Si vous rencontrez des difficultés, vous pouvez consulter notre centre d’aide ou nous en faire part à l’adresse email <a href="mailto:support@seves.beta.gouv.fr">support@seves.beta.gouv.fr</a>.
        <br/>Merci de ne pas répondre directement à ce message.</p>
    </div>
    </html>
        """,
    )


def notify_remove_permission(contact_agent: Contact, active_groups: list[str]):
    full_group_name = format_groups_for_email(active_groups)
    send(
        recipients=f"{contact_agent.agent.prenom} {contact_agent.agent.nom} <{contact_agent.email}>",
        subject=f"[Sèves {'/'.join(active_groups)}] - Droits d'accès",
        message=f"""
    Bonjour,
    Les droits d’accès vous ont été retirés pour Sèves {full_group_name}.
    Vous ne pouvez désormais plus accéder à Sèves.
    S’il s’agit d’une erreur, merci de contacter : support@seves.beta.gouv.fr
        """,
        html_message=f"""
    <!DOCTYPE html>
    <html>
    <div style="font-family: Arial, sans-serif;">
        <p style="font-weight: bold;">Droits d’accès Sèves</p>
        <p>Bonjour,</p>
        <p>Les droits d’accès vous ont été retirés pour Sèves {full_group_name}.</p>
        <p>Vous ne pouvez désormais plus accéder à Sèves.</p>
        <p>S’il s’agit d’une erreur, merci de contacter : <a href="mailto:support@seves.beta.gouv.fr">support@seves.beta.gouv.fr</a></p>
    </div>
    </html>
        """,
    )
