from django.views.generic import ListView

from sa.models import Evenement


class EvenementListView(ListView):
    paginate_by = 100
    context_object_name = "objects"
    model = Evenement
