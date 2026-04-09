from django.core.management.base import BaseCommand

from core.antivirus import scan_document
from core.models import Document


class Command(BaseCommand):
    help = "Run antivirus scan on files hosted in an S3 like bucket."
    BATCH_SIZE = 200

    def handle(self, *args, **options):
        documents_to_analyze = Document._base_manager.exclude(file="").filter(is_infected__isnull=True)
        documents_to_analyze[: self.BATCH_SIZE].select_for_update()

        for document in documents_to_analyze:
            is_infected = scan_document(document)
            if is_infected is not None:
                document.is_infected = scan_document(document)
                document.save(update_fields=["is_infected"])

        self.stdout.write(f"Analyzed {documents_to_analyze.count()} documents")
