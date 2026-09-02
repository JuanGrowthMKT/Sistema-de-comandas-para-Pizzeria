import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crea o resetea el superusuario/admin desde variables de entorno DJANGO_ADMIN_USERNAME / DJANGO_ADMIN_PASSWORD."

    def handle(self, *args, **options):
        user_model = get_user_model()
        username = os.environ.get("DJANGO_ADMIN_USERNAME") or "admin"
        password = os.environ.get("DJANGO_ADMIN_PASSWORD")
        if not password:
            self.stdout.write(self.style.WARNING("DJANGO_ADMIN_PASSWORD no está definida; omito admin."))
            return

        user, created = user_model.objects.get_or_create(
            username=username,
            defaults={"is_staff": True, "is_superuser": True},
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Superusuario '{username}' creado."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Superusuario '{username}' ya existía."))

        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS(f"Contraseña de '{username}' actualizada."))
