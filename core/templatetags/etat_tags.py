from django import template

register = template.Library()

# Selection des classes CSS du composant badge du DSFR pour les états d'une fiche
# https://www.systeme-de-design.gouv.fr/elements-d-interface/composants/badge
ETATS_COLORS = {
    "en_cours": "success",  # Vert
    "conclu": "success",  # Vert
}


@register.filter(name="etat_color")
def etat_color(value):
    return ETATS_COLORS.get(value)
