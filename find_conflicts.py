import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def find_conflicts():
    from apps.plan_comptable.models import CompteComptable
    
    comptes = CompteComptable.objects.all().values_list('numero', flat=True)
    padded_dict = {}
    conflicts = []
    
    for numero in comptes:
        if len(numero) > 6:
            # We don't pad those, but they might be invalid
            padded = numero
        else:
            padded = numero.ljust(6, '0')
        
        if padded in padded_dict:
            conflicts.append((numero, padded_dict[padded], padded))
        else:
            padded_dict[padded] = numero
            
    if conflicts:
        print("Conflicts found:")
        for num, existing, padded in conflicts:
            print(f"- '{num}' and '{existing}' both map to '{padded}'")
    else:
        print("No conflicts found.")

if __name__ == "__main__":
    find_conflicts()
