from django.core.management.base import BaseCommand
from species.utils import update_herbie_hbvspecies


class Command(BaseCommand):
    help = 'Updates local species names from remote sources'

    def handle(self, *args, **kwargs):
        update_herbie_hbvspecies()
