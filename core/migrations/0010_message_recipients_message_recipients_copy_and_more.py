# Generated by Django 5.0.3 on 2024-07-18 13:24

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def add_user_to_message(apps, schema_editor):
    Message = apps.get_model("core", "Message")
    Contact = apps.get_model("core", "Contact")
    Structure = apps.get_model("core", "Structure")
    Agent = apps.get_model("core", "Agent")
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))

    try:
        user = User.objects.get(email="service_account@seves.com")
    except User.DoesNotExist:
        user = User.objects.create_user(username="service_account", email="service_account@seves.com")

    try:
        structure = Structure.objects.get(niveau1="service_account")
    except Structure.DoesNotExist:
        structure = Structure.objects.create(niveau1="service_account")

    try:
        agent = Agent.objects.get(user=user)
    except Agent.DoesNotExist:
        agent = Agent.objects.create(
            user=user, prenom="Service", nom="Account", structure_complete="Service account", structure=structure
        )

    try:
        contact = Contact.objects.get(email="service_account@seves.com")
    except Contact.DoesNotExist:
        contact = Contact.objects.create(agent=agent, email="service_account@seves.com")

    for message in Message.objects.all():
        message.sender = contact
        message.recipients.set([contact])
        message.save()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0009_agent_structure_alter_contact_options_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="message",
            name="recipients",
            field=models.ManyToManyField(related_name="messages_recipient", to="core.contact"),
        ),
        migrations.AddField(
            model_name="message",
            name="recipients_copy",
            field=models.ManyToManyField(
                related_name="messages_recipient_copy",
                to="core.contact",
            ),
        ),
        migrations.AddField(
            model_name="message",
            name="sender",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="messages",
                to="core.contact",
            ),
        ),
        migrations.AlterField(
            model_name="message",
            name="title",
            field=models.CharField(max_length=512, verbose_name="Titre"),
        ),
        migrations.RunPython(add_user_to_message, migrations.RunPython.noop),
    ]
