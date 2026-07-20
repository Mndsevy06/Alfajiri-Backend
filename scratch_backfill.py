import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.saisie.models import LigneEcriture

updated = 0
for l in LigneEcriture.objects.filter(dossier__isnull=True):
    if l.ecriture and l.ecriture.dossier:
        l.dossier = l.ecriture.dossier
        l.save()
        updated += 1

print(f"Updated {updated} lignes")
