import re

from playwright.sync_api import Page

from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.urls import reverse

from core.constants import SV_DOMAIN, SSA_DOMAIN
from core.factories import ContactAgentFactory
from seves import settings
from seves.settings import CAN_GIVE_ACCESS_GROUP

User = get_user_model()


def test_notification_is_send_when_add_permission(live_server, page: Page, mailoutbox, mocked_authentification_user):
    sv_group, _ = Group.objects.get_or_create(name=settings.SV_GROUP)
    ssa_group, _ = Group.objects.get_or_create(name=settings.SSA_GROUP)
    access_admin_group, _ = Group.objects.get_or_create(name=CAN_GIVE_ACCESS_GROUP)
    mocked_authentification_user.groups.add(access_admin_group, sv_group)
    contact_agent = ContactAgentFactory(agent__structure=mocked_authentification_user.agent.structure)

    page.goto(f"{live_server.url}/{reverse('handle-permissions')}")
    page.locator(f"input[id='sv_{contact_agent.agent.user.pk}']").click(force=True)
    page.get_by_role("button", name="Enregistrer les modifications").click()

    expected_content = f"""
    <!DOCTYPE html>
    <html>
    <div style="font-family: Arial, sans-serif;">
        <p style="font-weight: bold;">Droits d’accès Sèves</p>
        <p>Bonjour,</p>
        <p>Les droits d’accès vous ont été attribués pour Sèves {SV_DOMAIN}.</p>
        <p>Vous pouvez désormais accéder à Sèves au lien suivant : <a href="https://seves.beta.gouv.fr">Sèves</a></p>
    </div>
    </html>
    """
    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    content, _ = mail.alternatives[0]
    pattern = r"\s+"
    normalized_content = re.sub(pattern, "", content)
    normalized_expected = re.sub(pattern, "", expected_content)
    assert normalized_expected == normalized_content
    assert set(mail.to) == {f"{contact_agent.agent.prenom} {contact_agent.agent.nom} <{contact_agent.email}>"}
    assert mail.from_email == "Sèves <no-reply@beta.gouv.fr>"
    assert mail.subject == "[Sèves SV] - Droits d'accès"


def test_notification_is_send_when_add_permission_for_several_groups(
    live_server, page: Page, mailoutbox, mocked_authentification_user
):
    sv_group, _ = Group.objects.get_or_create(name=settings.SV_GROUP)
    ssa_group, _ = Group.objects.get_or_create(name=settings.SSA_GROUP)
    access_admin_group, _ = Group.objects.get_or_create(name=CAN_GIVE_ACCESS_GROUP)
    mocked_authentification_user.groups.add(access_admin_group, sv_group, ssa_group)
    contact_agent = ContactAgentFactory(agent__structure=mocked_authentification_user.agent.structure)

    page.goto(f"{live_server.url}/{reverse('handle-permissions')}")
    page.locator(f"input[id='sv_{contact_agent.agent.user.pk}']").click(force=True)
    page.locator(f"input[id='ssa_{contact_agent.agent.user.pk}']").click(force=True)
    page.get_by_role("button", name="Enregistrer les modifications").click()

    expected_content = f"""
    <!DOCTYPE html>
    <html>
    <div style="font-family: Arial, sans-serif;">
        <p style="font-weight: bold;">Droits d’accès Sèves</p>
        <p>Bonjour,</p>
        <p>Les droits d’accès vous ont été attribués pour Sèves {SV_DOMAIN} et {SSA_DOMAIN}.</p>
        <p>Vous pouvez désormais accéder à Sèves au lien suivant : <a href="https://seves.beta.gouv.fr">Sèves</a></p>
    </div>
    </html>
    """
    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    content, _ = mail.alternatives[0]
    pattern = r"\s+"
    normalized_content = re.sub(pattern, "", content)
    normalized_expected = re.sub(pattern, "", expected_content)
    assert normalized_expected == normalized_content
    assert set(mail.to) == {f"{contact_agent.agent.prenom} {contact_agent.agent.nom} <{contact_agent.email}>"}
    assert mail.from_email == "Sèves <no-reply@beta.gouv.fr>"
    assert mail.subject == "[Sèves SV/SSA] - Droits d'accès"


def test_notification_is_send_when_remove_permission(live_server, page: Page, mailoutbox, mocked_authentification_user):
    sv_group, _ = Group.objects.get_or_create(name=settings.SV_GROUP)
    ssa_group, _ = Group.objects.get_or_create(name=settings.SSA_GROUP)
    access_admin_group, _ = Group.objects.get_or_create(name=CAN_GIVE_ACCESS_GROUP)
    mocked_authentification_user.groups.add(access_admin_group, sv_group)
    contact_agent = ContactAgentFactory(
        agent__structure=mocked_authentification_user.agent.structure, with_active_agent=True
    )
    contact_agent.agent.user.groups.add(sv_group)

    page.goto(f"{live_server.url}/{reverse('handle-permissions')}")
    page.locator(f"input[id='sv_{contact_agent.agent.user.pk}']").click(force=True)
    page.get_by_role("button", name="Enregistrer les modifications").click()

    expected_content = f"""
    <!DOCTYPE html>
    <html>
    <div style="font-family: Arial, sans-serif;">
        <p style="font-weight: bold;">Droits d’accès Sèves</p>
        <p>Bonjour,</p>
        <p>Les droits d’accès vous ont été retirés pour Sèves {SV_DOMAIN}.</p>
        <p>Vous ne pouvez désormais plus accéder à Sèves.</p>
        <p>S’il s’agit d’une erreur, merci de contacter : <a href="mailto:support@seves.beta.gouv.fr">support@seves.beta.gouv.fr</a></p>
    </div>
    </html>
    """
    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    content, _ = mail.alternatives[0]
    pattern = r"\s+"
    normalized_content = re.sub(pattern, "", content)
    normalized_expected = re.sub(pattern, "", expected_content)
    assert normalized_expected == normalized_content
    assert set(mail.to) == {f"{contact_agent.agent.prenom} {contact_agent.agent.nom} <{contact_agent.email}>"}
    assert mail.from_email == "Sèves <no-reply@beta.gouv.fr>"
    assert mail.subject == "[Sèves SV] - Droits d'accès"


def test_notification_is_send_when_remove_permission_for_several_groups(
    live_server, page: Page, mailoutbox, mocked_authentification_user
):
    sv_group, _ = Group.objects.get_or_create(name=settings.SV_GROUP)
    ssa_group, _ = Group.objects.get_or_create(name=settings.SSA_GROUP)
    access_admin_group, _ = Group.objects.get_or_create(name=CAN_GIVE_ACCESS_GROUP)
    mocked_authentification_user.groups.add(access_admin_group, sv_group, ssa_group)
    contact_agent = ContactAgentFactory(
        agent__structure=mocked_authentification_user.agent.structure, with_active_agent=True
    )
    contact_agent.agent.user.groups.add(sv_group, ssa_group)

    page.goto(f"{live_server.url}/{reverse('handle-permissions')}")
    page.locator(f"input[id='sv_{contact_agent.agent.user.pk}']").click(force=True)
    page.locator(f"input[id='ssa_{contact_agent.agent.user.pk}']").click(force=True)
    page.get_by_role("button", name="Enregistrer les modifications").click()

    expected_content = f"""
    <!DOCTYPE html>
    <html>
    <div style="font-family: Arial, sans-serif;">
        <p style="font-weight: bold;">Droits d’accès Sèves</p>
        <p>Bonjour,</p>
        <p>Les droits d’accès vous ont été retirés pour Sèves {SV_DOMAIN} et {SSA_DOMAIN}.</p>
        <p>Vous ne pouvez désormais plus accéder à Sèves.</p>
        <p>S’il s’agit d’une erreur, merci de contacter : <a href="mailto:support@seves.beta.gouv.fr">support@seves.beta.gouv.fr</a></p>
    </div>
    </html>
    """
    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    content, _ = mail.alternatives[0]
    pattern = r"\s+"
    normalized_content = re.sub(pattern, "", content)
    normalized_expected = re.sub(pattern, "", expected_content)
    assert normalized_expected == normalized_content
    assert set(mail.to) == {f"{contact_agent.agent.prenom} {contact_agent.agent.nom} <{contact_agent.email}>"}
    assert mail.from_email == "Sèves <no-reply@beta.gouv.fr>"
    assert mail.subject == "[Sèves SV/SSA] - Droits d'accès"
