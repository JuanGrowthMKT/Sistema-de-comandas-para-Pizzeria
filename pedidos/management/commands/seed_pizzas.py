from django.core.management.base import BaseCommand
from django.core import management

from pedidos.models import Pizza


class Command(BaseCommand):
    help = "Carga las pizzas iniciales desde el fixture solo si la tabla está vacía."

    def handle(self, *args, **options):
        if Pizza.objects.exists():
            self.stdout.write(self.style.SUCCESS("Pizzas ya cargadas; omito seed."))
            return
        management.call_command("loaddata", "pizzas", verbosity=1)
        self.stdout.write(self.style.SUCCESS("Pizzas iniciales cargadas."))