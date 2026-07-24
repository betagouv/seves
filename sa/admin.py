from django.contrib import admin

from .models import Espece, EvenementAnimal, Maladie

admin.site.register(EvenementAnimal)
admin.site.register(Maladie)
admin.site.register(Espece)
