import os
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Copia la base de datos SQLite a un archivo de respaldo con fecha (y prune los viejos)."

    def handle(self, *args, **options):
        db = settings.DATABASES['default']['NAME']
        if not os.path.exists(db):
            self.stdout.write(self.style.WARNING('No existe la base de datos; omito backup.'))
            return

        backup_dir = os.environ.get('BACKUP_DIR', os.path.join(os.path.dirname(db), 'backups'))
        os.makedirs(backup_dir, exist_ok=True)

        from django.utils import timezone
        stamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        dest = os.path.join(backup_dir, f'db_{stamp}.sqlite3')
        shutil.copy2(db, dest)
        self.stdout.write(self.style.SUCCESS(f'Backup: {dest}'))

        # Mantener solo los ultimos N backups
        keep = int(os.environ.get('BACKUP_KEEP', '7'))
        backups = sorted(
            (os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.startswith('db_') and f.endswith('.sqlite3')),
            key=os.path.getmtime,
        )
        while len(backups) > keep:
            old = backups.pop(0)
            os.remove(old)
            self.stdout.write(f'Eliminado backup viejo: {old}')
