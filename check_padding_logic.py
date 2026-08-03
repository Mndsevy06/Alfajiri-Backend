import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def check_mouvementable():
    from apps.plan_comptable.models import CompteComptable
    
    comptes = CompteComptable.objects.all()
    mouvementable_count = comptes.filter(mouvementable=True).count()
    print(f"Total comptes: {comptes.count()}")
    print(f"Comptes mouvementables: {mouvementable_count}")
    
    # Check conflicts if we only pad those with length >= 4
    for min_len in [2, 3, 4]:
        c_list = comptes.filter(numero__length__gte=min_len).values_list('numero', flat=True)
        padded_dict = {}
        conflicts = 0
        for num in c_list:
            padded = num.ljust(6, '0')
            if padded in padded_dict:
                conflicts += 1
            else:
                padded_dict[padded] = num
        print(f"Conflicts if padding only length >= {min_len}: {conflicts}")

if __name__ == "__main__":
    from django.db.models.functions import Length
    from django.db.models import CharField
    CharField.register_lookup(Length)
    check_mouvementable()
