from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sv", "0122_add_on_phytophthora_kernoviae"),
    ]

    operations = [
        migrations.DeleteModel(
            name="SiteInspection",
        ),
        migrations.AlterField(
            model_name="lieu",
            name="site_inspection",
            field=models.CharField(
                choices=[
                    (
                        "Plein air - zone de production",
                        [
                            ("CHAMP_CULTURE_PATURAGE", "Champ (culture, pâturage)"),
                            ("VERGER_VIGNE", "Verger/vigne"),
                            ("PEPINIERE", "Pépinière"),
                            ("FORET", "Forêt"),
                        ],
                    ),
                    (
                        "Plein air - autre",
                        [
                            ("JARDINS_PRIVES", "Jardins privés"),
                            ("SITES_PUBLICS", "Sites publics"),
                            ("ZONE_PROTEGEE", "Zone protégée"),
                            (
                                "PLANTES_SAUVAGES_HORS_ZONES_PROTEGEES",
                                "Plantes sauvages en dehors des zones protégées",
                            ),
                            (
                                "PLATEFORME_LOGISTIQUE_TRANSIT_STOCKAGE_OU_REVENTE_BOIS",
                                "Site commercial qui utilise du bois d'emballage",
                            ),
                            ("JARDINERIE_PLEIN_AIR", "Jardinerie"),
                            (
                                "RESEAU_IRRIGATION_DRAINAGE",
                                "Réseau d'irrigation ou de drainage",
                            ),
                            ("ZONE_HUMIDE", "Zone humide"),
                            ("INDUSTRIE_BOIS_PLEIN_AIR", "Industrie du bois"),
                            ("POINTS_ENTREE_PLEIN_AIR", "Points d'entrée"),
                            ("ZONES_RISQUE_PLEIN_AIR", "Zones à risque"),
                            (
                                "AEROPORT_PORT_ROUTE_VOIE_FERREE",
                                "Aéroport, port, route, voie ferrée",
                            ),
                            (
                                "MARCHES_REVENDEURS_MAGASINS_GROSSISTES",
                                "Marchés, revendeurs, magasins, grossistes",
                            ),
                            ("ZONES_URBAINES", "Zones urbaines"),
                            (
                                "BOIS_EMBALLAGE_PALETTES_EN_BOIS",
                                "Bois d'emballage, palettes en bois",
                            ),
                            ("CONTROLES_DES_MOUVEMENTS", "Contrôles des mouvements"),
                            (
                                "AUTRE_PLEIN_AIR",
                                "Autre (plein air) - préciser dans les commentaires",
                            ),
                        ],
                    ),
                    (
                        "Environnement fermé",
                        [
                            ("SERRE", "Serre"),
                            (
                                "SITE_PRIVE_AUTRE_QUE_SERRE",
                                "Site privé autre qu'une serre",
                            ),
                            (
                                "SITE_PUBLIC_AUTRE_QUE_SERRE",
                                "Site public autre qu'une serre",
                            ),
                            (
                                "SITE_COMMERCIAL_UTILISANT_BOIS_EMBALLAGE",
                                "Site commercial qui utilise du bois d'emballage",
                            ),
                            ("JARDINERIE_ENVIRONNEMENT_FERME", "Jardinerie"),
                            ("INDUSTRIE_BOIS_ENVIRONNEMENT_FERME", "Industrie du bois"),
                            ("AEROPORT_PORT_GARE", "Aéroport, port, gare"),
                            ("ZONES_RISQUE_ENVIRONNEMENT_FERME", "Zones à risque"),
                            (
                                "ACTIVITES_CONDITIONNEMENT_ENTREPOT",
                                "Activités de conditionnement, entrepôt",
                            ),
                            (
                                "GROSSISTES_MARCHES_DETAILLANTS",
                                "Grossistes, marchés, détaillants",
                            ),
                            (
                                "AUTRE_ENVIRONNEMENT_FERME",
                                "Autre (environnement fermé) - préciser dans les commentaires",
                            ),
                        ],
                    ),
                    (
                        "Inconnu",
                        [("INCONNU", "Inconnu - préciser dans les commentaires")],
                    ),
                ],
                default="INCONNU",
                verbose_name="Site d'inspection",
            ),
        ),
    ]
