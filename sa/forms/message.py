from core.fields import ContactModelMultipleChoiceField
from core.forms import BaseCompteRenduDemandeInterventionForm
from core.models import Contact


class CompteRenduDemandeInterventionForm(BaseCompteRenduDemandeInterventionForm):
    recipients = ContactModelMultipleChoiceField(
        queryset=Contact.objects.structures_only().prefetch_related("structure"), label="Destinataires", required=True
    )
