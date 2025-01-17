import datetime

from django.db import models, transaction


class NumeroFiche(models.Model):
    class Meta:
        unique_together = ("annee", "numero")
        verbose_name = "Numéro de fiche"
        verbose_name_plural = "Numéros de fiche"
        db_table = "sv_numero_fiche"

    annee = models.IntegerField(verbose_name="Année")
    numero = models.IntegerField(verbose_name="Numéro")

    def __str__(self):
        return f"{self.annee}.{self.numero}"

    def _save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    @classmethod
    @transaction.atomic  # Assure que la méthode est exécutée dans une transaction pour éviter les race conditions
    def get_next_numero(cls):
        annee_courante = datetime.datetime.now().year
        last_fiche = cls.objects.filter(annee=annee_courante).order_by("-numero").first()

        # Si une fiche existe déjà pour cette année
        # On incrémente le numéro
        # Si aucune fiche n'existe pour cette année
        # On réinitialise le numéro à 1
        if last_fiche is not None:
            numero = last_fiche.numero + 1
        else:
            numero = 1

        new_fiche = cls(annee=annee_courante, numero=numero)
        new_fiche._save()
        return new_fiche


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


# TODO RM ME
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

    @classmethod
    def get_etat_cloture(cls):
        return cls.objects.get(libelle=cls.CLOTURE)

    def __str__(self):
        return self.libelle


class StatutEtablissement(models.Model):
    class Meta:
        verbose_name = "Statut de l'établissement"
        verbose_name_plural = "Statuts de l'établissement"
        db_table = "sv_statut_etablissement"

    libelle = models.CharField(max_length=100, verbose_name="Libellé", unique=True)

    def __str__(self):
        return self.libelle
