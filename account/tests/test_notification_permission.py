import re

from playwright.sync_api import Page

from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.urls import reverse

from core.factories import ContactAgentFactory
from seves import settings

User = get_user_model()


def test_notification_is_send_when_add_permission(live_server, page: Page, mailoutbox, mocked_authentification_user):
    sv_group, _ = Group.objects.get_or_create(name=settings.SV_GROUP)
    group, _ = Group.objects.get_or_create(name="access_admin")
    mocked_authentification_user.groups.add(group)
    contact_agent = ContactAgentFactory(agent__structure=mocked_authentification_user.agent.structure)
    contact_agent.agent.user.groups.add(sv_group)

    page.goto(f"{live_server.url}/{reverse('handle-permissions')}")
    page.get_by_text(str(contact_agent)).click()
    page.get_by_role("button", name="Enregistrer les modifications").click()

    expected_content = """
<!DOCTYPE html>
<html>
<div style="font-family: Arial, sans-serif;">
    <p>Bonjour,</p>
    <p>Nous vous informons que vos droits d’accès ont été ouverts avec succès.</p>
    <p>
        Vous pouvez désormais accéder à Sèves Santé des végétaux en utilisant vos identifiants Agricoll habituels :
        <a href="https://seves.beta.gouv.fr">Sèves</a>
    </p>
    <p>Si vous rencontrez des difficultés ou si vous avez des questions, n’hésitez pas à nous contacter.</p>
    <p>Bien cordialement,</p>
    <p>L’équipe Sèves</p>
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
    assert mail.subject == "Sèves Santé des végétaux - Ouverture de vos droits d'accès"


def test_notification_is_send_when_remove_permission(live_server, page: Page, mailoutbox, mocked_authentification_user):
    sv_group, _ = Group.objects.get_or_create(name=settings.SV_GROUP)
    group, _ = Group.objects.get_or_create(name="access_admin")
    mocked_authentification_user.groups.add(group)
    contact_agent = ContactAgentFactory(
        agent__structure=mocked_authentification_user.agent.structure, with_active_agent=True
    )
    contact_agent.agent.user.groups.add(sv_group)

    page.goto(f"{live_server.url}/{reverse('handle-permissions')}")
    page.get_by_text(str(contact_agent)).click()
    page.get_by_role("button", name="Enregistrer les modifications").click()

    expected_content = """
<!DOCTYPE html>
<html>
<div style="font-family: Arial, sans-serif;">
    <p>Bonjour,</p>
    <p>Nous vous informons que vos droits d’accès ont été supprimés.</p>
    <p>Vous ne pouvez donc désormais plus accéder à Sèves Santé des végétaux.</p>
    <p>S’il s’agit d’une erreur, veuillez nous nous contacter.</p>
    <p>Bien cordialement,</p>
    <p>L’équipe Sèves</p>
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
    assert mail.subject == "Sèves Santé des végétaux - Suppression de vos droits d'accès"
