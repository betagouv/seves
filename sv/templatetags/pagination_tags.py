"""
Tag 'url_replace' pour la gestion des URLs dans la pagination.

Ce tag permet de :
1. Conserver les paramètres de recherche lors de la navigation entre les pages de résultats.
2. Modifier dynamiquement l'URL pour inclure à la fois le numéro de la page et les paramètres de recherche actuels.
3. Prévenir la duplication des paramètres dans l'URL, évitant ainsi des erreurs et des comportements inattendus.
Cela se produit parce que request.GET.urlencode inclut déjà le paramètre page dans l'URL.
Lors de l'ajout de ?page={{ i }}&{{ request.GET.urlencode }} dans le template, il y a ajout d'un deuxième paramètre page à l'URL.

Utilisation : Ce tag peut être réutilisé dans différents templates pour une gestion cohérente des URLs de pagination tout en conservant les paramètres de filtrage.
"""

from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    query = context["request"].GET.copy()
    for k, v in kwargs.items():
        query[k] = v
    return query.urlencode()
