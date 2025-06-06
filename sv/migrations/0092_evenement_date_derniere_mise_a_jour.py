# Generated by Django 5.1.8 on 2025-04-23 13:57

from django.db import migrations, models


def get_versions_from_ids(apps, ids, model):
    ContentType = apps.get_model("contenttypes", "ContentType")
    Version = apps.get_model("reversion", "Version")

    if not ids:
        return []
    content_type = ContentType.objects.get_for_model(model)
    return Version.objects.select_related("revision__user__agent__structure").filter(
        content_type=content_type, object_id__in=list(ids)
    )


def latest_version_fiche_zone_delimitee(apps, fiche_zone_delimitee):
    ZoneInfestee = apps.get_model("sv", "ZoneInfestee")
    Version = apps.get_model("reversion", "Version")
    ContentType = apps.get_model("contenttypes", "ContentType")

    zone_infestees = ZoneInfestee.objects.filter(fiche_zone_delimitee_id=fiche_zone_delimitee.pk).values_list(
        "id", flat=True
    )
    zone_infestees_versions = get_versions_from_ids(apps, zone_infestees, ZoneInfestee)
    instance_version = (
        Version.objects.filter(
            content_type=ContentType.objects.get_for_model(fiche_zone_delimitee), object_id=fiche_zone_delimitee.pk
        )
        .select_related("revision__user__agent__structure")
        .first()
    )
    versions = list(zone_infestees_versions) + [instance_version]
    versions = [v for v in versions if v]
    if not versions:
        return None
    return max(versions, key=lambda obj: obj.revision.date_created)


def lastest_version_fiche_detection(apps, fiche_detection):
    Lieu = apps.get_model("sv", "Lieu")
    Prelevement = apps.get_model("sv", "Prelevement")
    Version = apps.get_model("reversion", "Version")
    ContentType = apps.get_model("contenttypes", "ContentType")

    lieu_versions = get_versions_from_ids(apps, [lieu.id for lieu in fiche_detection.lieux.all()], Lieu)
    prelevements = Prelevement.objects.filter(lieu__fiche_detection__pk=fiche_detection.pk).values_list("id", flat=True)
    prelevement_versions = get_versions_from_ids(apps, prelevements, Prelevement)
    instance_version = (
        Version.objects.filter(
            content_type=ContentType.objects.get_for_model(fiche_detection), object_id=fiche_detection.pk
        )
        .select_related("revision__user__agent__structure")
        .first()
    )
    versions = list(lieu_versions) + list(prelevement_versions) + [instance_version]
    versions = [v for v in versions if v]
    if not versions:
        return None
    return max(versions, key=lambda obj: obj.revision.date_created)


def latest_version_evenement(apps, evenement):
    Version = apps.get_model("reversion", "Version")
    ContentType = apps.get_model("contenttypes", "ContentType")

    detections_latest_versions = [
        lastest_version_fiche_detection(apps, fiche_detection)
        for fiche_detection in evenement.detections.filter(is_deleted=False)
    ]
    zone_latest_version = (
        latest_version_fiche_zone_delimitee(apps, evenement.fiche_zone_delimitee)
        if evenement.fiche_zone_delimitee
        else None
    )
    instance_version = (
        Version.objects.filter(content_type=ContentType.objects.get_for_model(evenement), object_id=evenement.pk)
        .select_related("revision")
        .select_related("revision__user__agent__structure")
        .first()
    )
    versions = list(detections_latest_versions) + [zone_latest_version, instance_version]
    versions = [v for v in versions if v]
    if not versions:
        return None
    return max(versions, key=lambda obj: obj.revision.date_created)


def init_date_derniere_mise_a_jour(apps, schema_editor):
    Evenement = apps.get_model("sv", "Evenement")
    FicheDetection = apps.get_model("sv", "FicheDetection")
    FicheZoneDelimitee = apps.get_model("sv", "FicheZoneDelimitee")

    for evenement in Evenement.objects.all():
        if latest_version := latest_version_evenement(apps, evenement):
            Evenement.objects.filter(pk=evenement.pk).update(
                date_derniere_mise_a_jour=latest_version.revision.date_created
            )

        if detections := evenement.detections.filter(is_deleted=False):
            for fiche_detection in detections:
                if latest_version := lastest_version_fiche_detection(apps, fiche_detection):
                    FicheDetection.objects.filter(pk=fiche_detection.pk).update(
                        date_derniere_mise_a_jour=latest_version.revision.date_created
                    )

        if fiche_zone_delimitee := evenement.fiche_zone_delimitee:
            if latest_version := latest_version_fiche_zone_delimitee(apps, fiche_zone_delimitee):
                FicheZoneDelimitee.objects.filter(pk=fiche_zone_delimitee.pk).update(
                    date_derniere_mise_a_jour=latest_version.revision.date_created
                )


class Migration(migrations.Migration):
    dependencies = [
        ("sv", "0091_prelevement_date_rapport_analyse"),
    ]

    operations = [
        migrations.AddField(
            model_name="evenement",
            name="date_derniere_mise_a_jour",
            field=models.DateTimeField(
                auto_now=True, db_index=True, null=True, verbose_name="Date dernière mise à jour"
            ),
        ),
        migrations.AddField(
            model_name="fichedetection",
            name="date_derniere_mise_a_jour",
            field=models.DateTimeField(
                auto_now=True, db_index=True, null=True, verbose_name="Date dernière mise à jour"
            ),
        ),
        migrations.AddField(
            model_name="fichezonedelimitee",
            name="date_derniere_mise_a_jour",
            field=models.DateTimeField(
                auto_now=True, db_index=True, null=True, verbose_name="Date dernière mise à jour"
            ),
        ),
        migrations.RunPython(init_date_derniere_mise_a_jour, migrations.RunPython.noop),
    ]
