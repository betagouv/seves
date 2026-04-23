from django.db import migrations, models
from django.db.models import Q

CHOICES = [
    ("CHAMP_CULTURE_PATURAGE", "Champ (culture, pâturage)"),
    ("VERGER_VIGNE", "Verger/vigne"),
    ("PEPINIERE", "Pépinière"),
    ("FORET", "Forêt"),
    ("JARDINS_PRIVES", "Jardins privés (plein air)"),
    ("SITES_PUBLICS", "Sites publics (plein air)"),
    (
        "ZONE_PROTEGEE",
        "Espaces réglementés pour la préservation de l'environnement (plein air)",
    ),
    (
        "PLANTES_SAUVAGES_HORS_ZONES_PROTEGEES",
        "Plantes sauvages dans des aires non protégées (plein air)",
    ),
    (
        "PLATEFORME_LOGISTIQUE_TRANSIT_STOCKAGE_OU_REVENTE_BOIS",
        "Plateforme logistique de transit, stockage ou revente de bois d'emballage (plein air)",
    ),
    ("JARDINERIE_PLEIN_AIR", "Jardinerie (plein air)"),
    (
        "RESEAU_IRRIGATION_DRAINAGE",
        "Réseau d'irrigation ou de drainage",
    ),
    ("ZONE_HUMIDE", "Zone humide"),
    ("INDUSTRIE_BOIS_PLEIN_AIR", "Industrie du bois (plein air)"),
    ("POINTS_ENTREE_PLEIN_AIR", "Points d'entrée (plein air)"),
    ("ZONES_RISQUE_PLEIN_AIR", "Zones à risque (plein air)"),
    (
        "AEROPORT_PORT_ROUTE_VOIE_FERREE",
        "Aéroport, port, route, voie ferrée (plein air)",
    ),
    (
        "MARCHES_REVENDEURS_MAGASINS_GROSSISTES",
        "Marchés, détaillants, magasins, grossistes (plein air)",
    ),
    ("ZONES_URBAINES", "Zones urbaines (plein air)"),
    (
        "BOIS_EMBALLAGE_PALETTES_EN_BOIS",
        "Emballages en bois, palettes en bois (plein air)",
    ),
    (
        "CONTROLES_DES_MOUVEMENTS",
        "Contrôles en circulation (plein air)",
    ),
    ("AUTRE_PLEIN_AIR", "Autre (plein air)"),
    ("SERRE", "Serre"),
    (
        "SITE_PRIVE_AUTRE_QUE_SERRE",
        "Site privé (environnement fermé) autre qu'une serre",
    ),
    (
        "SITE_PUBLIC_AUTRE_QUE_SERRE",
        "Site public (environnement fermé) autre qu'une serre",
    ),
    (
        "SITE_COMMERCIAL_UTILISANT_BOIS_EMBALLAGE",
        "Installations couvertes et closes de transit, stockage ou revente de bois d'emballage",
    ),
    (
        "JARDINERIE_ENVIRONNEMENT_FERME",
        "Jardinerie (environnement fermé)",
    ),
    (
        "INDUSTRIE_BOIS_ENVIRONNEMENT_FERME",
        "Industrie du bois (environnement fermé)",
    ),
    (
        "AEROPORT_PORT_GARE",
        "Aéroport, port, gare (environnement fermé)",
    ),
    (
        "ZONES_RISQUE_ENVIRONNEMENT_FERME",
        "Zones à risque (environnement fermé)",
    ),
    (
        "ACTIVITES_CONDITIONNEMENT_ENTREPOT",
        "Usine d'emballage, entrepôt (environnement fermé)",
    ),
    (
        "GROSSISTES_MARCHES_DETAILLANTS",
        "Grossistes, marchés, détaillants (environnement fermé)",
    ),
    ("AUTRE_ENVIRONNEMENT_FERME", "Autre (environnement fermé)"),
    ("INCONNU", "Inconnu - préciser dans les commentaires"),
]


def migrate_site_inspection(apps, _):
    by_label = {label: value for value, label in CHOICES}
    Lieu = apps.get_model("sv", "Lieu")

    sitenames = Lieu.objects.filter(site_inspection__isnull=False).values_list("site_inspection__nom", flat=True)
    for name in sitenames:
        Lieu.objects.filter(site_inspection__nom=name).update(site_inspection_new=by_label[name])


def unmigrate_site_inspection(apps, _):
    by_value = dict(CHOICES)
    Lieu = apps.get_model("sv", "Lieu")
    SiteInspection = apps.get_model("sv", "SiteInspection")

    sitenames = Lieu.objects.filter(~Q(site_inspection_new="INCONNU")).values_list("site_inspection_new", flat=True)
    for name in sitenames:
        Lieu.objects.filter(site_inspection_new=name).update(
            site_inspection=SiteInspection.objects.get(nom=by_value[name])
        )


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("sv", "0120_auto_20260424_1058"),
    ]

    operations = [
        migrations.AddField(
            model_name="lieu",
            name="site_inspection_new",
            field=models.CharField(
                choices=CHOICES,
                default="INCONNU",
                verbose_name="Site d'inspection",
            ),
        ),
        migrations.RunPython(migrate_site_inspection, reverse_code=unmigrate_site_inspection),
        migrations.RemoveField(
            model_name="lieu",
            name="site_inspection",
        ),
        migrations.RenameField(
            model_name="lieu",
            old_name="site_inspection_new",
            new_name="site_inspection",
        ),
    ]
