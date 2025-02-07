from django.db import models


class OrganismeNuisible(models.Model):
    class Meta:
        verbose_name = "Organisme nuisible"
        verbose_name_plural = "Organismes nuisibles"
        db_table = "sv_organisme_nuisible"
        constraints = [
            models.UniqueConstraint(
                fields=["code_oepp", "libelle_court"], name="unique_organisme_nuisible_code_libelle"
            )
        ]

    code_oepp = models.CharField(verbose_name="Code OEPP", unique=True)
    libelle_court = models.CharField(max_length=255, verbose_name="Nom", unique=True)
    libelle_long = models.CharField(max_length=255, verbose_name="Nom", unique=True)

    def __str__(self):
        return self.libelle_court


class StatutReglementaire(models.Model):
    class Meta:
        verbose_name = "Statut règlementaire de l'organisme"
        verbose_name_plural = "Statuts règlementaires de l'organisme"
        db_table = "sv_statut_reglementaire"
        constraints = [
            models.UniqueConstraint(fields=["code", "libelle"], name="unique_statut_reglementaire_code_libelle")
        ]

    code = models.CharField(max_length=10, verbose_name="Code", unique=True)
    libelle = models.CharField(max_length=100, verbose_name="Libellé", unique=True)

    def __str__(self):
        return self.libelle


class Etat(models.Model):
    NOUVEAU = "nouveau"
    EN_COURS = "en cours"
    CLOTURE = "clôturé"

    class Meta:
        verbose_name = "Etat"
        verbose_name_plural = "Etats"
        db_table = "sv_etat"

    libelle = models.CharField(max_length=30, unique=True)

    @classmethod
    def get_etat_initial(cls):
        return cls.objects.get(libelle=cls.NOUVEAU).id


class StatutEtablissement(models.Model):
    class Meta:
        verbose_name = "Statut de l'établissement"
        verbose_name_plural = "Statuts de l'établissement"
        db_table = "sv_statut_etablissement"

    libelle = models.CharField(max_length=100, verbose_name="Libellé", unique=True)

    def __str__(self):
        return self.libelle
