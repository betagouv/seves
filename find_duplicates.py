from django.db.models import Count
from django.apps import apps

models_and_fields = [
    ("sv.OrganismeNuisible", "code_oepp"),
    ("sv.OrganismeNuisible", "libelle_court"),
    ("sv.StatutReglementaire", "code"),
    ("sv.StatutReglementaire", "libelle"),
    ("sv.Contexte", "nom"),
    ("sv.StatutEtablissement", "libelle"),
    ("sv.PositionChaineDistribution", "libelle"),
    ("sv.StructurePreleveur", "nom"),
    ("sv.SiteInspection", "nom"),
    ("sv.MatricePrelevee", "libelle"),
    ("sv.EspeceEchantillon", "code_oepp"),
    ("sv.EspeceEchantillon", "libelle"),
    ("sv.LaboratoireAgree", "nom"),
    ("sv.LaboratoireConfirmationOfficielle", "nom"),
    ("sv.StatutEvenement", "libelle"),
]


def find_duplicates():
    for model_name, field_name in models_and_fields:
        model = apps.get_model(model_name)
        duplicates = model.objects.values(field_name).annotate(count=Count("id")).filter(count__gt=1)

        if duplicates:
            print(f"Doublons trouvés dans le modèle {model_name} pour le champ {field_name}:")
            for duplicate in duplicates:
                duplicate_values = model.objects.filter(**{field_name: duplicate[field_name]}).values_list(
                    "id", flat=True
                )
                print(f"Valeur dupliquée: {duplicate[field_name]}, IDs: {list(duplicate_values)}")
        else:
            print(f"Aucun doublon trouvé dans le modèle {model_name} pour le champ {field_name}.")


find_duplicates()
