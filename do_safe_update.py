import os
import django
from django.db import connection, transaction

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def safe_update():
    from apps.plan_comptable.models import CompteComptable
    
    comptes = CompteComptable.objects.all().values_list('numero', flat=True)
    
    # 1. Check for conflicts
    to_pad = []
    padded_dict = set(comptes)
    conflicts = []
    
    for numero in comptes:
        if 4 <= len(numero) < 6:
            padded = numero.ljust(6, '0')
            if padded != numero:
                to_pad.append((numero, padded))

    from collections import defaultdict
    pad_groups = defaultdict(list)
    for old, new in to_pad:
        pad_groups[new].append(old)
        
    for new, olds in pad_groups.items():
        if len(olds) > 1:
            conflicts.append(f"Multiple accounts {olds} pad to {new}")
        elif new in padded_dict and new not in [o for o, n in to_pad]:
            conflicts.append(f"Account {olds[0]} pads to {new} which already exists in DB")

    if conflicts:
        print("Conflicts found with >= 4 length rule:")
        for c in conflicts:
            print("-", c)
        
        # Let's see if there's an alternative, like only movementable accounts
        return
        
    print(f"No conflicts. Ready to update {len(to_pad)} accounts...")
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE plan_comptable_comptecomptable 
                SET numero = RPAD(numero, 6, '0') 
                WHERE LENGTH(numero) >= 4 AND LENGTH(numero) < 6;
            """)
            print(f"Update successful! Rows updated: {cursor.rowcount}")
    except Exception as e:
        print(f"Error during SQL update: {e}")

if __name__ == "__main__":
    safe_update()
