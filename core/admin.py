from django.contrib import admin
from django.utils.html import format_html
from post_office.admin import EmailAdmin
from post_office.models import Email

from .models import Agent, AuditLog, Contact, Departement, Document, Export, FinSuiviContact, Message, Region, Structure

admin.site.register(Document)
admin.site.register(Message)


class AgentAdmin(admin.ModelAdmin):
    search_fields = ("nom", "prenom", "user__email")
    raw_id_fields = ("user",)


class StructureAdmin(admin.ModelAdmin):
    list_display = ("niveau1", "niveau2", "libelle")
    search_fields = ("niveau1", "niveau2", "libelle")


class ContactAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "structure", "agent")
    list_filter = ("structure", "agent")
    search_fields = ("email", "agent__nom", "agent__prenom")


class ExportAdmin(admin.ModelAdmin):
    pass


class AuditLogAdmin(admin.ModelAdmin):
    search_fields = ("ip", "action", "user__email")
    raw_id_fields = ("user",)
    readonly_fields = ("created_at",)


admin.site.unregister(Email)


class CustomEmailAdmin(EmailAdmin):
    @admin.display(description="HTML Body")
    def render_html_body(self, instance):
        return format_html(
            '<iframe srcdoc="{}" style="width: 700px; min-height: 500px; border: 1px solid #ccc;"></iframe>',
            instance.html_message,
        )


admin.site.register(Agent, AgentAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(Export, ExportAdmin)
admin.site.register(FinSuiviContact)
admin.site.register(Departement)
admin.site.register(Region)
admin.site.register(AuditLog, AuditLogAdmin)
admin.site.register(Structure, StructureAdmin)
admin.site.register(Email, CustomEmailAdmin)
