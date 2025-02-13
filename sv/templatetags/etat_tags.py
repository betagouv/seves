from django import template

register = template.Library()

# Selection des classes CSS du composant badge du DSFR pour les états d'une fiche
# https://www.systeme-de-design.gouv.fr/elements-d-interface/composants/badge
ETATS_FICHE_COLORS = {
    "en_cours": "success",  # Vert
    "cloture": "error",  # Rouge
    "fin de suivi": "warning",  # Orange
}


@register.filter(name="etat_fiche_color")
def etat_fiche_color(value):
    return ETATS_FICHE_COLORS.get(value)
