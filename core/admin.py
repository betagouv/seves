from django.contrib import admin
from .models import Document, Structure, Contact, Agent, Message, FinSuiviContact


admin.site.register(Document)
admin.site.register(Message)
admin.site.register(Agent)


class StructureAdmin(admin.ModelAdmin):
    list_display = ("niveau1", "niveau2", "libelle")


admin.site.register(Structure, StructureAdmin)


class ContactAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "structure", "agent")
    list_filter = ("structure", "agent")


admin.site.register(Contact, ContactAdmin)
admin.site.register(FinSuiviContact)
