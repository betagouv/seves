import csv
from collections import defaultdict
from datetime import datetime

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from core.constants import MUS_STRUCTURE
from core.models import Structure, Visibilite
from sv.constants import KNOWN_OEPP_CODES_FOR_STATUS_REGLEMENTAIRES
from sv.models import (
    FicheDetection,
    StatutEvenement,
    OrganismeNuisible,
    Contexte,
    Prelevement,
    StructurePreleveuse,
    SiteInspection,
    EspeceEchantillon,
    MatricePrelevee,
    Laboratoire,
    Departement,
    Lieu,
    FicheZoneDelimitee,
    ZoneInfestee,
    StatutReglementaire,
    Etat,
    Evenement,
)
from django.db import transaction, IntegrityError, DataError
import requests
import re

errors = defaultdict(set)
ERROR_REPORT = True


def _get_get_data_from_insee_code(insee_code):
    response = requests.get(f"https://geo.api.gouv.fr/communes/{insee_code}?fields=departement")
    data = response.json()
    return {"name": data["nom"], "code": data["code"], "departement": data["departement"]["nom"]}


def _get_get_data_from_city_name(name):
    response = requests.get(f"https://geo.api.gouv.fr/communes?nom={name}&fields=departement")
    data = response.json()
    if not data:
        return None
    return {"name": data[0]["nom"], "code": data[0]["code"], "departement": data[0]["departement"]["nom"]}


def get_geo_data(data):
    try:
        insee_code = int(data)
        return _get_get_data_from_insee_code(insee_code)
    except ValueError:
        name = data
        return _get_get_data_from_city_name(name)


def get_geo_position(lat, long):
    if "X" in lat and "Y" in long:
        coord_1 = lat.replace("X", "").replace(":", "").replace(" ", "").replace("Y", "").replace(",", ".")
        coord_2 = long.replace("Y", "").replace(":", "").replace(" ", "").replace("X", "").replace(",", ".")
        try:
            if float(coord_1) > 200000 and float(coord_2) > 6000000:
                return {"lambert93_latitude": coord_2, "lambert93_longitude": coord_1}
            if float(coord_2) > 200000 and float(coord_1) > 6000000:
                return {"lambert93_latitude": coord_1, "lambert93_longitude": coord_2}
        except ValueError:
            return None
        return None
    if "°" in lat and "°" in long:
        lat = lat.replace("'' ", '"').replace("′", "'").replace(" ", "").replace("″", '"')
        deg, minutes, seconds, direction = re.split("[°'\"]", lat)
        new_lat = (float(deg) + float(minutes) / 60 + float(seconds) / (60 * 60)) * (
            -1 if direction in ["W", "S"] else 1
        )

        long = long.replace("'' ", '"').replace("′", "'").replace(" ", "").replace("″", '"')
        deg, minutes, seconds, direction = re.split("[°'\"]", long)
        new_long = (float(deg) + float(minutes) / 60 + float(seconds) / (60 * 60)) * (
            -1 if direction in ["W", "S"] else 1
        )
        return {"wgs84_longitude": new_long, "wgs84_latitude": new_lat}

    if "," in lat and "," in long:
        try:
            return {"wgs84_longitude": float(long.replace(",", ".")), "wgs84_latitude": float(lat.replace(",", "."))}
        except ValueError:
            return None

    if "." in lat and "." in long:
        try:
            return {"wgs84_longitude": float(long), "wgs84_latitude": float(lat)}
        except ValueError:
            return None


class Command(BaseCommand):
    help = "Permet d'importer l'historique existant"

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str)

    def _get_instance_from_fk(self, data, model_class, field_key, allow_empty, num=""):
        if not data:
            if allow_empty:
                return None
            errors[num].add(f"La valeur {data} pour le modèle {model_class.__name__} ne peut pas être vide")

        try:
            obj = model_class._base_manager.get(**{field_key: data})
        except model_class.DoesNotExist:
            errors[num].add(
                f"La valeur {data} pour le modèle {model_class.__name__} n'est pas autorisée (pour le champ final {field_key})"
            )
            raise
        except model_class.MultipleObjectsReturned:
            errors[num].add(
                f"La valeur {data} pour le modèle {model_class.__name__} n'est pas assez explicite, plusieurs valeurs trouvées"
            )
            raise
        return obj

    def _get_geo_data(self, row):
        try:
            geo_data = get_geo_data(row["Zone_Nom_commune-Code_INSEE"])
        except Exception:
            errors[row["Alerte_num_MUS"]].add(f"Cant read geo data : {row['Zone_Nom_commune-Code_INSEE']}")
        if geo_data:
            departement = self._get_instance_from_fk(
                geo_data["departement"], Departement, "nom__iexact", allow_empty=False, num=row["Alerte_num_MUS"]
            )
            return {"commune": geo_data["name"], "code_insee": geo_data["code"], "departement": departement}

        data = row["Zone_departement"].split("(")[0].strip()
        departement = self._get_instance_from_fk(
            data, Departement, "nom__iexact", allow_empty=True, num=row["Alerte_num_MUS"]
        )
        return {"departement": departement}

    def _get_geo_position(self, row):
        geo_position = get_geo_position(row["Echantillon_lat_WGS84"], row["Echantillon_long_WGS84"])
        if geo_position:
            return geo_position

        if row["Echantillon_lat_WGS84"] not in [None, "", " "]:
            errors[row["Alerte_num_MUS"]].add(
                f"Incorrect geo position values : {row['Echantillon_lat_WGS84']} {row['Echantillon_long_WGS84']}"
            )
        return {}

    def _get_date_notif(self, row):
        if row["Alerte_date_notif_DGAL"]:
            return datetime.strptime(row["Alerte_date_notif_DGAL"], "%d/%m/%Y %H:%M")

    def _get_date_prelevement(self, row):
        if row["Echantillon_date_prelvement"]:
            date_prelevement = row["Echantillon_date_prelvement"].replace("\xa0", "")
            try:
                return datetime.strptime(date_prelevement, "%d/%m/%Y")
            except ValueError:
                return datetime.strptime(date_prelevement, "%d/%m/%y")

    def _get_date_premier_signalement(self, row):
        if row["Signalement_date_suspicion"]:
            date_prelevement = row["Signalement_date_suspicion"].replace("\xa0", "")
            try:
                return datetime.strptime(date_prelevement, "%d/%m/%Y")
            except ValueError:
                try:
                    return datetime.strptime(date_prelevement, "%d/%m/%y")
                except ValueError:
                    errors[row["Alerte_num_MUS"]].add("Can't parse date premier signalement")

    def _surface(self, surface_str, row):
        try:
            if "km²" in surface_str:
                return float(
                    surface_str.replace("km²", "").replace(",", ".").strip()
                ), ZoneInfestee.UnitesSurfaceInfesteeTotale.KILOMETRE_CARRE
            if "m²" in surface_str or "m2" in surface_str:
                return float(
                    surface_str.replace("m²", "").replace("m2", "").strip()
                ), ZoneInfestee.UnitesSurfaceInfesteeTotale.METRE_CARRE
        except ValueError:
            errors[row["Alerte_num_MUS"]].add(f"Can't parse surface {surface_str}")
            return None, None

        if "ha" in surface_str:
            left, right = surface_str.split("ha")
            try:
                return float(f"{left.strip()}.{right.strip()}"), ZoneInfestee.UnitesSurfaceInfesteeTotale.HECTARE
            except ValueError:
                try:
                    surface_str = surface_str.replace("ha", "").replace(",", ".").strip()
                    return float(surface_str), ZoneInfestee.UnitesSurfaceInfesteeTotale.HECTARE
                except ValueError:
                    pass

        errors[row["Alerte_num_MUS"]].add(f"Can't parse surface {surface_str}")
        return None, None

    def _rayon(self, rayon_str, row, field):
        rayon_str = rayon_str.lower().replace(",", ".")
        if "km" in rayon_str:
            try:
                return float(rayon_str.replace("km", "").strip()), FicheZoneDelimitee.UnitesRayon.KILOMETRE
            except ValueError:
                errors[row["Alerte_num_MUS"]].add(f"Cant parse rayon to float {rayon_str} - {field}")
        if "m" in rayon_str:
            try:
                return float(rayon_str.replace("m", "").strip()), FicheZoneDelimitee.UnitesRayon.METRE
            except ValueError:
                errors[row["Alerte_num_MUS"]].add(f"Cant parse rayon to float {rayon_str} - {field}")

        errors[row["Alerte_num_MUS"]].add(f"Cant parse rayon {rayon_str} - {field}")
        return None, None

    def _get_commentaire(self, row):
        commentaire = ""
        if row["Signalement_contexte"]:
            commentaire += f"Commentaire contexte de signalement : {row['Signalement_contexte']} \n"
        if row["Analyse_commentaires"]:
            commentaire += f"Commentaire analyse : {row['Analyse_commentaires']} \n"
        if row["Commentaires"]:
            commentaire += row["Commentaires"]
        return commentaire

    def handle(self, *args, **options):
        createur = Structure.objects.get(niveau2=MUS_STRUCTURE)
        default_structure, _ = StructurePreleveuse._base_manager.get_or_create(nom="Import historique")
        default_structure.is_active = False
        default_structure.save()
        default_laboratoire, _ = Laboratoire._base_manager.get_or_create(
            nom="Import historique", confirmation_officielle=True
        )
        default_laboratoire.is_active = False
        default_laboratoire.save()
        etat = Evenement.Etat.EN_COURS

        with open(options["file"]) as csvfile:
            reader = csv.DictReader(csvfile, delimiter=";")
            for i, row in enumerate(reader):
                print(row["Alerte_num_MUS"])
                status = None
                if row["Alerte_classification"]:
                    try:
                        status = StatutEvenement.objects.get(libelle__iexact=row["Alerte_classification"])
                    except Exception:
                        if ERROR_REPORT:
                            errors[row["Alerte_num_MUS"]].add(
                                "La valeur de la colonne Alerte_classification ne peut pas être lue"
                            )
                            continue
                        else:
                            raise

                organisme = None
                if row["ON_code_OEPP"]:
                    try:
                        organisme = self._get_instance_from_fk(
                            row["ON_code_OEPP"].strip(" "),
                            OrganismeNuisible,
                            "code_oepp__iexact",
                            allow_empty=False,
                            num=row["Alerte_num_MUS"],
                        )
                    except Exception:
                        if ERROR_REPORT:
                            continue
                        else:
                            raise
                elif row["ON_nom_scientifique"]:
                    try:
                        organisme = self._get_instance_from_fk(
                            row["ON_nom_scientifique"],
                            OrganismeNuisible,
                            "libelle_long__icontains",
                            allow_empty=False,
                            num=row["Alerte_num_MUS"],
                        )
                    except Exception:
                        if ERROR_REPORT:
                            continue
                        else:
                            raise
                else:
                    errors[row["Alerte_num_MUS"]].add("Pas de valeur pour l'organisme nuisible via le code ou le nom")

                statut_reglementaire = None
                if organisme is not None:
                    for code, oepps in KNOWN_OEPP_CODES_FOR_STATUS_REGLEMENTAIRES.items():
                        if organisme.code_oepp in oepps:
                            statut_reglementaire = StatutReglementaire.objects.get(code=code)

                if statut_reglementaire is None:
                    statut_reglementaire = StatutReglementaire.objects.first()
                    errors[row["Alerte_num_MUS"]].add(
                        f"Impossible de trouver le statut pour le code oepp {organisme.code_oepp}"
                    )

                data = row["Signalement_origine"]
                context = None
                if data:
                    try:
                        data = row["Signalement_origine"].split(". ")[1]
                    except IndexError:
                        errors[row["Alerte_num_MUS"]].add(
                            "La valeur de la colonne Signalement_origine ne peut pas être lue"
                        )
                        continue
                    if data == "Autre : préciser":
                        data = "autre (à préciser dans le fil de suivi)"
                    context = self._get_instance_from_fk(
                        data, Contexte, "nom__icontains", allow_empty=False, num=row["Alerte_num_MUS"]
                    )

                data = row["Echantillon_structure_prelevement"]
                try:
                    if data == "OVS":
                        data = "Délégataire"
                    if data == "":
                        data = "Import historique"
                    structure = self._get_instance_from_fk(
                        data, StructurePreleveuse, "nom__iexact", allow_empty=False, num=row["Alerte_num_MUS"]
                    )
                except Exception:
                    if ERROR_REPORT:
                        continue
                    else:
                        raise

                data = row["Echantillon_site_prelevement"]
                if data == "autres":
                    data = "Autre (à préciser dans le fil de suivi)"
                try:
                    site = self._get_instance_from_fk(
                        data, SiteInspection, "nom__iexact", allow_empty=True, num=row["Alerte_num_MUS"]
                    )
                except Exception:
                    if ERROR_REPORT:
                        continue
                    else:
                        raise

                data = row["Echantillon_type"]
                try:
                    matrice = self._get_instance_from_fk(
                        data, MatricePrelevee, "libelle__iexact", allow_empty=True, num=row["Alerte_num_MUS"]
                    )
                except MatricePrelevee.DoesNotExist:
                    if ERROR_REPORT:
                        continue
                    else:
                        raise

                espece = None
                data = row["Echantillon_Code_OEPP_espece_vegetale"]
                if data:
                    try:
                        espece = self._get_instance_from_fk(
                            data, EspeceEchantillon, "code_oepp", allow_empty=True, num=row["Alerte_num_MUS"]
                        )
                    except Exception:
                        if ERROR_REPORT:
                            continue
                        else:
                            raise
                else:
                    data = row["Echantillon_Nom_espece_vegetale"]
                    try:
                        self._get_instance_from_fk(
                            data, EspeceEchantillon, "libelle__iexact", allow_empty=True, num=row["Alerte_num_MUS"]
                        )
                    except Exception:
                        if ERROR_REPORT:
                            continue
                        else:
                            raise

                labo_premiere_intention = None
                if row["Analyse_nom_Lab_1"]:
                    try:
                        labo_premiere_intention = Laboratoire._base_manager.get(nom=row["Analyse_nom_Lab_1"])
                    except Laboratoire.DoesNotExist:
                        labo_premiere_intention = Laboratoire.objects.create(
                            nom=row["Analyse_nom_Lab_1"], is_active=False
                        )

                labo_confirm = None
                if row["Analyse_nom_lab_confirm_officielle"]:
                    try:
                        labo_confirm = Laboratoire._base_manager.get(nom=row["Analyse_nom_lab_confirm_officielle"])
                    except Laboratoire.DoesNotExist:
                        labo_confirm = Laboratoire.objects.create(
                            nom=row["Analyse_nom_lab_confirm_officielle"], is_active=False, confirmation_officielle=True
                        )

                if len(row["Alerte_num_IMSOC"]) <= 9:
                    rasff = row["Alerte_num_IMSOC"]
                else:
                    rasff = ""
                    errors[row["Alerte_num_MUS"]].add("Le numéro RASFF est trop long")

                resultat = Prelevement.Resultat.NON_DETECTE
                if row["détecté"]:
                    resultat = Prelevement.Resultat.DETECTE

                is_officiel = row["officiel"] == "Officiel"

                annee, numero = row["Alerte_num_MUS"].split("/")
                numero = numero.lstrip("0")
                existing_event = Evenement.objects.filter(numero_annee=annee, numero_evenement=numero).first()
                rayon_data = {}
                if row["ZD_rayon_ZT"]:
                    rayon, unit = self._rayon(row["ZD_rayon_ZT"], row, "ZD_rayon_ZT")
                    if rayon and unit:
                        rayon_data = {"rayon_zone_tampon": rayon, "unite_rayon_zone_tampon": unit}

                if existing_event:
                    if organisme != existing_event.organisme_nuisible:
                        errors[row["Alerte_num_MUS"]].add(
                            "Problème de cohérence d'organisme nuisible entre les différentes lignes"
                        )
                    if statut_reglementaire != existing_event.statut_reglementaire:
                        errors[row["Alerte_num_MUS"]].add(
                            "Problème de cohérence de statut_reglementaire entre les différentes lignes"
                        )
                    if (
                        existing_event.fiche_zone_delimitee
                        and existing_event.fiche_zone_delimitee.commentaire != row["ZD_Contexte_Commentaire"]
                    ):
                        errors[row["Alerte_num_MUS"]].add(
                            "Problème de cohérence de commentaire ZD entre les différentes lignes"
                        )
                    if (
                        existing_event.fiche_zone_delimitee
                        and rayon_data.get("rayon_zone_tampon")
                        and existing_event.fiche_zone_delimitee.rayon_zone_tampon != rayon_data["rayon_zone_tampon"]
                    ):
                        errors[row["Alerte_num_MUS"]].add(
                            "Problème de cohérence de rayon zone tampon entre les différentes lignes"
                        )
                    if (
                        existing_event.fiche_zone_delimitee
                        and rayon_data.get("unite_rayon_zone_tampon")
                        and existing_event.fiche_zone_delimitee.unite_rayon_zone_tampon
                        != rayon_data["unite_rayon_zone_tampon"]
                    ):
                        errors[row["Alerte_num_MUS"]].add(
                            "Problème de cohérence de d'unite de zone tampon entre les différentes lignes"
                        )

                with transaction.atomic():
                    if existing_event:
                        evenement = existing_event
                    else:
                        evenement = Evenement.objects.create(
                            numero_annee=annee,
                            numero_evenement=numero,
                            organisme_nuisible=organisme,
                            createur=createur,
                            statut_reglementaire=statut_reglementaire,
                            visibilite=Visibilite.NATIONALE,
                            etat=etat,
                        )

                    fiche = FicheDetection.objects.create(
                        numero_rasff=rasff,
                        statut_evenement=status,
                        date_creation=self._get_date_notif(row),
                        contexte=context,
                        createur=createur,
                        commentaire=self._get_commentaire(row),
                        mesures_conservatoires_immediates=row["Mesures_consignation"],
                        date_premier_signalement=self._get_date_premier_signalement(row),
                        mesures_phytosanitaires=row["Mesures_eradication"],
                        mesures_surveillance_specifique=row["Mesures_surveillance"],
                        vegetaux_infestes=row["ZD_Nb_vegetaux_infestes"],
                        evenement=evenement,
                    )

                    try:
                        geo_data = self._get_geo_data(row)
                    except Exception:
                        if ERROR_REPORT:
                            errors[row["Alerte_num_MUS"]].add(
                                f"Impossible de devinier la ville depuis la ban: {row['Zone_Nom_commune-Code_INSEE']}"
                            )
                        else:
                            raise
                    geo_position = self._get_geo_position(row)

                    adresse_lieu_dit = row["Lieu_dit_adresse_nom_operateur"]
                    if len(adresse_lieu_dit) > 100:
                        adresse_lieu_dit = adresse_lieu_dit[0:97] + "..."

                    lieu = Lieu.objects.create(
                        nom="Lieu",
                        fiche_detection=fiche,
                        **geo_data,
                        **geo_position,
                        site_inspection=site,
                        adresse_lieu_dit=adresse_lieu_dit,
                    )

                    try:
                        date_prelevement = self._get_date_prelevement(row)
                    except ValueError:
                        errors[row["Alerte_num_MUS"]].add("Impossible de lire la valeur de date_prelevement")
                        continue

                    numero_ri = ""
                    if (
                        is_officiel
                        and row["Echantillon_num_inspection_resytal"]
                        and row["Echantillon_num_inspection_resytal"] != "/"
                    ):
                        numero_ri = row["Echantillon_num_inspection_resytal"].strip()

                    try:
                        Prelevement.objects.create(
                            type_analyse=Prelevement.TypeAnalyse.PREMIERE_INTENTION,
                            is_officiel=is_officiel,
                            numero_echantillon=row["Echantillon_num_phytopass"],
                            numero_rapport_inspection=numero_ri,
                            structure_preleveuse=structure,
                            date_prelevement=date_prelevement,
                            matrice_prelevee=matrice,
                            espece_echantillon=espece,
                            laboratoire=labo_premiere_intention,
                            lieu=lieu,
                            resultat=resultat,
                        )
                    except IntegrityError as e:
                        errors[row["Alerte_num_MUS"]].add("Contrainte check_numero_officiel_empty_or_null")
                        continue
                    except DataError as e:
                        errors[row["Alerte_num_MUS"]].add("Une des valeurs est trop longue")
                        continue

                    if labo_confirm:
                        if labo_confirm.nom in ("LDA 22", "LABOCEA", "LDA 67"):
                            type_analyse = Prelevement.TypeAnalyse.PREMIERE_INTENTION
                        else:
                            type_analyse = Prelevement.TypeAnalyse.CONFIRMATION

                        try:
                            Prelevement.objects.create(
                                type_analyse=type_analyse,
                                is_officiel=True,
                                numero_echantillon=row["Echantillon_num_phytopass"],
                                numero_rapport_inspection=numero_ri,
                                structure_preleveuse=structure,
                                date_prelevement=date_prelevement,
                                matrice_prelevee=matrice,
                                espece_echantillon=espece,
                                laboratoire=labo_confirm,
                                lieu=lieu,
                                resultat=resultat,
                            )
                        except ValidationError as e:
                            try:
                                Prelevement.objects.create(
                                    type_analyse=type_analyse,
                                    is_officiel=True,
                                    numero_echantillon=row["Echantillon_num_phytopass"],
                                    numero_rapport_inspection=numero_ri,
                                    structure_preleveuse=structure,
                                    date_prelevement=date_prelevement,
                                    matrice_prelevee=matrice,
                                    espece_echantillon=espece,
                                    laboratoire=default_laboratoire,
                                    lieu=lieu,
                                    resultat=resultat,
                                )
                            except ValidationError as e:
                                errors[row["Alerte_num_MUS"]].add(e.message)
                                errors[row["Alerte_num_MUS"]].add(
                                    f"Labo concerné {labo_confirm} et {default_laboratoire}"
                                )

                    caracteristique = ""
                    if row["ZD_Contexte"]:
                        data = row["ZD_Contexte"].replace(";", "").strip().strip(".").strip(" ").lower()
                        try:
                            caracteristique = next(
                                value
                                for value, label in ZoneInfestee.CaracteristiquePrincipale.choices
                                if label.lower() == data
                            )
                        except:
                            errors[row["Alerte_num_MUS"]].add(
                                f"Impossible de lire la valeur ZD_Contexte: {row['ZD_Contexte']}"
                            )
                            continue

                    if existing_event and existing_event.fiche_zone_delimitee:
                        print(f"Skipping zone {numero}")
                        continue
                    else:
                        fiche_zone = FicheZoneDelimitee.objects.create(
                            createur=createur, **rayon_data, commentaire=row["ZD_Contexte_Commentaire"]
                        )
                        print("Adding FDZ to evenement")
                        print(evenement)
                        evenement.fiche_zone_delimitee = fiche_zone
                        evenement.save()
                    if row["ZD_surface_ZI"].strip() or row["ZD_rayon_ZI"].strip():
                        surface_data = {}
                        if row["ZD_surface_ZI"]:
                            surface, unit = self._surface(row["ZD_surface_ZI"], row)
                            surface_data = {
                                "surface_infestee_totale": surface,
                                "unite_surface_infestee_totale": unit
                                or ZoneInfestee.UnitesSurfaceInfesteeTotale.METRE_CARRE,
                            }

                        rayon_data = {}
                        if row["ZD_rayon_ZI"]:
                            rayon, unit_rayon = self._rayon(row["ZD_rayon_ZI"], row, "ZD_rayon_ZI")
                            rayon_data = {
                                "rayon": rayon,
                                "unite_rayon": unit_rayon or ZoneInfestee.UnitesRayon.KILOMETRE,
                            }

                        ZoneInfestee.objects.create(
                            fiche_zone_delimitee=fiche_zone,
                            caracteristique_principale=caracteristique,
                            **surface_data,
                            **rayon_data,
                        )
        print(len(errors.keys()))

        for k, values in errors.items():
            print(k)
            for value in values:
                print(f"    - {value}")


# TODO gérer les dates de création date_creation
