from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from django.db.models import OuterRef, Subquery, Prefetch
from .models import FicheDetection, Lieu

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
