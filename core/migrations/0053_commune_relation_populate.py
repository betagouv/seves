from logging import getLogger

from django.db import migrations
from django.db.models import OuterRef, Subquery

logger = getLogger(__name__)


def populate_commmunes(apps, _):
    from core.migrations import libelle_pre_proccess

    SSAEtablissement = apps.get_model("ssa", "Etablissement")
    TIACEtablissement = apps.get_model("tiac", "Etablissement")
    Lieu = apps.get_model("sv", "Lieu")
    Commune = apps.get_model("core", "Commune")

    for Model in (TIACEtablissement, SSAEtablissement, Lieu):
        Model.objects.exclude(code_insee="").update(
            new_commune=Subquery(Commune.objects.filter(code_insee=OuterRef("code_insee")).distinct().values_list("id"))
        )
        cached = {}
        skip = set()
        qs = list(
            Model.objects.annotate(libelle=libelle_pre_proccess("commune")).filter(code_insee="").exclude(libelle="")
        )
        for record in qs:
            try:
                if record.libelle in skip:
                    logger.info(f"Skipping commune with libelle {record.libelle} yielding multiple records")
                    continue

                if record.libelle not in cached:
                    cached[record.libelle] = Commune.objects.annotate(
                        libelle=libelle_pre_proccess("libelle_acheminement")
                    ).get(libelle=record.libelle)

                record.new_commune = cached[record.libelle]
                record.save()
            except Commune.MultipleObjectsReturned:
                skip.add(record.libelle)
                logger.info(f"Multiple communes found with libelle {record.libelle}")
            except Commune.DoesNotExist:
                pass
            except Exception as e:
                logger.exception(e)

        logger.info(f"Processed {len(qs)} records")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0052_commune"),
        ("ssa", "0062_etablissement_new_commune"),
        ("tiac", "0047_etablissement_new_commune"),
        ("sv", "0113_lieu_new_commune"),
    ]

    operations = [migrations.RunPython(populate_commmunes)]
