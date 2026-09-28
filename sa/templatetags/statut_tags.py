from django import template

from sa.models.evenement import StatutEvenement

register = template.Library()


STATUTS_COLORS = {
    StatutEvenement.SUSPECT.value: "fr-badge--green-tilleul-verveine",
    StatutEvenement.CONFIRME.value: "fr-badge--error",
    StatutEvenement.NON_RETENU.value: "fr-badge--info",
}


@register.filter(name="statut_color")
def statut_color(value):
    return STATUTS_COLORS.get(value)
