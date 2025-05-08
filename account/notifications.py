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
    Les droits d’accès vous ont été attribués pour {full_group_name}.
    Vous pouvez désormais accéder à Sèves au lien suivant : https://seves.beta.gouv.fr
        """,
        html_message=f"""
    <!DOCTYPE html>
    <html>
    <div style="font-family: Arial, sans-serif;">
        <p style="font-weight: bold;">Droits d’accès Sèves</p>
        <p>Bonjour,</p>
        <p>Les droits d’accès vous ont été attribués pour {full_group_name}.</p>
        <p>Vous pouvez désormais accéder à Sèves au lien suivant : <a href="https://seves.beta.gouv.fr">Sèves</a></p>
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
    Les droits d’accès vous ont été retirés pour {full_group_name}.
    Vous ne pouvez désormais plus accéder à Sèves.
    S’il s’agit d’une erreur, merci de contacter : support@seves.beta.gouv.fr
        """,
        html_message=f"""
    <!DOCTYPE html>
    <html>
    <div style="font-family: Arial, sans-serif;">
        <p style="font-weight: bold;">Droits d’accès Sèves</p>
        <p>Bonjour,</p>
        <p>Les droits d’accès vous ont été retirés pour {full_group_name}</p>
        <p>Vous ne pouvez désormais plus accéder à Sèves.</p>
        <p>S’il s’agit d’une erreur, merci de contacter : <a href="mailto:support@seves.beta.gouv.fr">support@seves.beta.gouv.fr</a></p>
    </div>
    </html>
        """,
    )
