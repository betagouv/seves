import json
from datetime import datetime
import uuid
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, DetailView, CreateView, View, UpdateView
from django.urls import reverse
from django.db.models import OuterRef, Subquery, Prefetch
from django.http import HttpResponseBadRequest, HttpResponseRedirect, HttpResponse
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib import messages
from .models import (
	FicheDetection, Lieu, PrelevementOfficiel, PrelevementNonOfficiel, Unite, StatutEvenement, OrganismeNuisible,
	StatutReglementaire, Contexte, StructurePreleveur, SiteInspection, MatricePrelevee, EspeceEchantillon,
	LaboratoireAgree, LaboratoireConfirmationOfficielle, NumeroFiche, Departement
)


class HomeView(TemplateView):
	template_name = "sv/index.html"


class FicheDetectionListView(ListView):
	model = FicheDetection
	ordering = ['-numero']

	def get_queryset(self):
		# Pour chaque fiche de détection, on récupère la liste des lieux associés
		lieux_prefetch = Prefetch('lieux', queryset=Lieu.objects.order_by('id'), to_attr='lieux_list')
		queryset = super().get_queryset().prefetch_related(lieux_prefetch)

		# Pour chaque fiche de détection, on récupère le nom de la région du premier lieu associé
		first_lieu = Lieu.objects.filter(fiche_detection=OuterRef('pk')).order_by('id')
		queryset = queryset.annotate(
			region=Subquery(first_lieu.values('departement__region__nom')[:1]),
		)

		return queryset
	

class FicheDetectionDetailView(DetailView):
	model = FicheDetection

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)

		# Ajout des lieux associés à la fiche de détection
		context['lieux'] = Lieu.objects.filter(fiche_detection=self.get_object())

		# Ajout des prélèvements officiels associés à chaque lieu
		prelevements_officiels = PrelevementOfficiel.objects.filter(lieu__fiche_detection=self.get_object())
		context['prelevements_officiels'] = prelevements_officiels

		# Ajout des prélèvements non officiels associés à chaque lieu
		prelevements_non_officiels = PrelevementNonOfficiel.objects.filter(lieu__fiche_detection=self.get_object())
		context['prelevements_non_officiels'] = prelevements_non_officiels

		return context


class FicheDetectionContextMixin:
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['departements'] = list(Departement.objects.values('id', 'numero', 'nom'))
		context['unites'] = list(Unite.objects.values('id', 'nom'))
		context['statuts_evenement'] = list(StatutEvenement.objects.values('id', 'libelle'))
		context['organismes_nuisibles'] = list(OrganismeNuisible.objects.values('id', 'libelle_court'))
		context['statuts_reglementaires'] = list(StatutReglementaire.objects.values('id', 'libelle'))
		context['contextes'] = list(Contexte.objects.values('id', 'nom'))
		context['structures_preleveurs'] = list(StructurePreleveur.objects.values('id', 'nom'))
		context['sites_inspections'] = list(SiteInspection.objects.values('id', 'nom'))
		context['matrices_prelevees'] = list(MatricePrelevee.objects.values('id', 'libelle'))
		context['especes_echantillon'] = list(EspeceEchantillon.objects.values('id', 'libelle'))
		context['laboratoires_agrees'] = list(LaboratoireAgree.objects.values('id', 'nom'))
		context['laboratoires_confirmation_officielle'] = list(LaboratoireConfirmationOfficielle.objects.values('id', 'nom'))
		return context


class FicheDetectionCreateView(FicheDetectionContextMixin, CreateView):
	model = FicheDetection
	fields = ['createur', 'statut_evenement', 'organisme_nuisible', 'statut_reglementaire', 'contexte', 'date_premier_signalement', 'commentaire', 'mesures_conservatoires_immediates', 'mesures_consignation', 'mesures_phytosanitaires', 'mesures_surveillance_specifique']

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['is_creation'] = True
		return context

	def post(self, request):
		# Récupération des données du formulaire
		data = request.POST
		localisations = json.loads(data['localisations'])
		prelevements = json.loads(data['prelevements'])

		# Validation des données
		errors = self.validate_data(data, localisations, prelevements)
		if errors:
			return HttpResponseBadRequest(json.dumps(errors))
		
		# Création des objets en base de données
		with transaction.atomic():
			fiche = self.create_fiche_detection(data)
			self.create_lieux(localisations, fiche)
			self.create_prelevements(prelevements, localisations)

		return HttpResponseRedirect(reverse('fiche-detection-vue-detaillee', args=[fiche.pk]))

	def validate_data(self, data, localisations, prelevements):	
		errors = []

		# createur est obligatoire
		if not data['createurId']:
			errors.append('Le champ createur est obligatoire')	
		elif not Unite.objects.filter(pk=data['createurId']).exists():
			errors.append('Le champ createur est invalide')
		
		# Validation des lieux (nom du lieu obligatoire)
		for loc in localisations:
			if not loc['nomLocalisation']:
				errors.append('Le champ nom du lieu est obligatoire')
			if loc['departementId'] and not Departement.objects.filter(pk=loc['departementId']).exists():
				errors.append('Le champ département est invalide')

		# Validation des prélèvements
		localisation_ids = [loc['id'] for loc in localisations]
		for prelevement in prelevements:
			# chaque prélèvement doit être associé à un lieu
			if prelevement['localisationId'] not in localisation_ids:
				errors.append(f"Le prélèvement avec l\'id {prelevement['id']} n\'est relié à aucune localisation")
			# structure preleveur doit être valide (existe en base de données)
			if prelevement['structurePreleveurId'] and not StructurePreleveur.objects.filter(pk=prelevement['structurePreleveurId']).exists():
				errors.append('Le champ structure preleveur est invalide')
			# site inspection doit être valide (existe en base de données)
			if prelevement['siteInspectionId'] and not SiteInspection.objects.filter(pk=prelevement['siteInspectionId']).exists():
				errors.append('Le champ site inspection est invalide')
			# matrice prelevée doit être valide (existe en base de données)
			if prelevement['matricePreleveeId'] and not MatricePrelevee.objects.filter(pk=prelevement['matricePreleveeId']).exists():
				errors.append('Le champ matrice prelevée est invalide')
			# si c'est un prélèvement officiel, laboratoire agréé et/ou laboratoireConfirmationOfficielleId doit être valide (existe en base de données)
			if prelevement['isPrelevementOfficiel']:
				if prelevement['laboratoireAgreeId'] and not LaboratoireAgree.objects.filter(pk=prelevement['laboratoireAgreeId']).exists():
					errors.append('Le champ laboratoire agréé est invalide')
				if prelevement['laboratoireConfirmationOfficielleId'] and not LaboratoireConfirmationOfficielle.objects.filter(pk=prelevement['laboratoireConfirmationOfficielleId']).exists():
					errors.append('Le champ laboratoire confirmation officielle est invalide')
		
		return errors
	
	def create_fiche_detection(self, data): 
		# format de la date de premier signalement
		date_premier_signalement = data['datePremierSignalement']
		try:
			datetime.strptime(date_premier_signalement, '%Y-%m-%d')
		except ValueError:
			date_premier_signalement = None
		
		# Création de la fiche de détection en base de données
		fiche = FicheDetection(
			numero=NumeroFiche.get_next_numero(),
			createur_id=data['createurId'],
			statut_evenement_id=data['statutEvenementId'],
			organisme_nuisible_id=data['organismeNuisibleId'],
			statut_reglementaire_id=data['statutReglementaireId'],
			contexte_id=data['contexteId'],
			date_premier_signalement=date_premier_signalement,
			commentaire=data['commentaire'],
			mesures_conservatoires_immediates=data['mesuresConservatoiresImmediates'],
			mesures_consignation=data['mesuresConsignation'],
			mesures_phytosanitaires=data['mesuresPhytosanitaires'],
			mesures_surveillance_specifique=data['mesuresSurveillanceSpecifique'],
		)
		fiche.save()

		return fiche
	
	def create_lieux(self, localisations, fiche):
		# Création des lieux en base de données
		for loc in localisations:
			wgs84_longitude = loc['coordGPSWGS84Longitude'] if loc['coordGPSWGS84Longitude'] != '' else None
			wgs84_latitude = loc['coordGPSWGS84Latitude'] if loc['coordGPSWGS84Latitude'] != '' else None

			#lieu = Lieu(fiche_detection=fiche, **loc)
			lieu = Lieu(fiche_detection=fiche, 
						nom=loc['nomLocalisation'], 
						wgs84_longitude=wgs84_longitude,
						wgs84_latitude=wgs84_latitude,
						adresse_lieu_dit=loc['adresseLieuDit'],
						commune=loc['commune'],
						code_insee=loc['codeINSEE'],
						departement_id=loc['departementId'])
			lieu.save()
			loc['lieu_pk'] = lieu.pk
		return localisations

	def create_prelevements(self, prelevements, localisations):
		# Création des prélèvements en base de données
		for prel in prelevements:
			# format de la date de prélèvement 
			try:
				datetime.strptime(prel['datePrelevement'], '%Y-%m-%d')
			except ValueError:
				prel['datePrelevement'] = None

			# recupérer le lieu_pk associé à chaque prélèvement prel
			prel['lieu_pk'] = next((loc['lieu_pk'] for loc in localisations if loc['id'] == prel['localisationId']), None)
			
			if prel['isPrelevementOfficiel']:
				prelevement_officiel = PrelevementOfficiel(lieu_id=prel['lieu_pk'],
															structure_preleveur_id=prel['structurePreleveurId'],
															numero_echantillon=prel['numeroEchantillon'],
															date_prelevement=prel['datePrelevement'],
															site_inspection_id=prel['siteInspectionId'],
															matrice_prelevee_id=prel['matricePreleveeId'],
															espece_echantillon_id=prel['especeEchantillonId'],
															numero_phytopass=prel['numeroPhytopass'],
															laboratoire_agree_id=prel['laboratoireAgreeId'],
															laboratoire_confirmation_officielle_id=prel['laboratoireConfirmationOfficielleId'])
				prelevement_officiel.save()
			else:
				prelevement_non_officiel = PrelevementNonOfficiel(lieu_id=prel['lieu_pk'],
																structure_preleveur_id=prel['structurePreleveurId'],
																numero_echantillon=prel['numeroEchantillon'],
																date_prelevement=prel['datePrelevement'],
																site_inspection_id=prel['siteInspectionId'],
																matrice_prelevee_id=prel['matricePreleveeId'],
																espece_echantillon_id=prel['especeEchantillonId'])
				prelevement_non_officiel.save()


class FicheDetectionUpdateView(FicheDetectionContextMixin, UpdateView):
	model = FicheDetection
	fields = ['createur', 'statut_evenement', 'organisme_nuisible', 'statut_reglementaire', 'contexte', 'date_premier_signalement', 'commentaire', 'mesures_conservatoires_immediates', 'mesures_consignation', 'mesures_phytosanitaires', 'mesures_surveillance_specifique']
	success_message = "La fiche détection a été modifiée avec succès."

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)

		# Lieux associés à la fiche de détection
		lieux = Lieu.objects.filter(fiche_detection=self.object).values()

		# Prélèvements officiels associés à chaque lieu
		prelevements_officiels = PrelevementOfficiel.objects.filter(lieu__fiche_detection=self.object).values()
		for prelevement in prelevements_officiels:
			prelevement['uuid'] = str(uuid.uuid4())
			prelevement['isPrelevementOfficiel'] = True
		
		# Prélèvements non officiels associés à chaque lieu
		prelevements_non_officiels = PrelevementNonOfficiel.objects.filter(lieu__fiche_detection=self.object).values()
		for prelevement in prelevements_non_officiels:
			prelevement['uuid'] = str(uuid.uuid4())
			prelevement['isPrelevementOfficiel'] = False
		
		context['is_creation'] = False
		context['lieux'] = list(lieux)
		context['prelevements_officiels'] = list(prelevements_officiels)
		context['prelevements_non_officiels'] = list(prelevements_non_officiels)

		return context

	def post(self, request, pk):
		data = request.POST

		# Validation
		errors = []
		# createur est obligatoire
		if not data['createurId']:
			errors.append('Le champ createur est obligatoire')	
		elif not Unite.objects.filter(pk=data['createurId']).exists():
			errors.append('Le champ createur est invalide')
		if errors:
			return HttpResponseBadRequest(json.dumps(errors))
		
		# Format de la date de premier signalement
		date_premier_signalement = data['datePremierSignalement']
		try:
			datetime.strptime(date_premier_signalement, '%Y-%m-%d')
		except ValueError:
			date_premier_signalement = None

		# Mise à jour des champs de l'objet FicheDetection
		fiche_detection = self.get_object()
		fiche_detection.createur_id = data.get('createurId')
		fiche_detection.statut_evenement_id = data.get('statutEvenementId')
		fiche_detection.organisme_nuisible_id = data.get('organismeNuisibleId')
		fiche_detection.statut_reglementaire_id = data.get('statutReglementaireId')
		fiche_detection.contexte_id = data.get('contexteId')
		fiche_detection.date_premier_signalement = date_premier_signalement
		fiche_detection.commentaire = data.get('commentaire')
		fiche_detection.mesures_conservatoires_immediates = data.get('mesuresConservatoiresImmediates')
		fiche_detection.mesures_consignation = data.get('mesuresConsignation')
		fiche_detection.mesures_phytosanitaires = data.get('mesuresPhytosanitaires')
		fiche_detection.mesures_surveillance_specifique = data.get('mesuresSurveillanceSpecifique')
		
		try:
			fiche_detection.full_clean()
			fiche_detection.save()
		except ValidationError as e:
			return HttpResponseBadRequest(str(e))
		
		messages.success(request, self.success_message)
		return redirect(reverse('fiche-detection-vue-detaillee', args=[fiche_detection.pk]))