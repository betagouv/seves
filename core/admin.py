from django.contrib import admin

from .models import Agent, AuditLog, Contact, Departement, Document, Export, FinSuiviContact, Message, Region, Structure

admin.site.register(Document)
admin.site.register(Message)
admin.site.register(Agent)


class StructureAdmin(admin.ModelAdmin):
    list_display = ("niveau1", "niveau2", "libelle")


admin.site.register(Structure, StructureAdmin)


class ContactAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "structure", "agent")
    list_filter = ("structure", "agent")
    search_fields = ("email", "agent__nom", "agent__prenom")


class ExportAdmin(admin.ModelAdmin):
    pass


class AuditLogAdmin(admin.ModelAdmin):
    search_fields = ("ip", "action", "user__email")
    raw_id_fields = ("user",)


admin.site.register(Contact, ContactAdmin)
admin.site.register(Export, ExportAdmin)
admin.site.register(FinSuiviContact)
admin.site.register(Departement)
admin.site.register(Region)
admin.site.register(AuditLog, AuditLogAdmin)
