import os
import django
from django.db import transaction

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

@transaction.atomic
def update_via_orm():
    from apps.plan_comptable.models import CompteComptable
    from apps.saisie.models import LigneEcriture
    
    comptes = list(CompteComptable.objects.all())
    updated_count = 0
    
    for old_compte in comptes:
        if 4 <= len(old_compte.numero) < 6:
            new_num = old_compte.numero.ljust(6, '0')
            if new_num == old_compte.numero:
                continue
                
            # Create a duplicate with the new PK
            # We copy all fields
            kwargs = {}
            for field in old_compte._meta.fields:
                kwargs[field.name] = getattr(old_compte, field.name)
            
            kwargs['numero'] = new_num
            new_compte = CompteComptable(**kwargs)
            new_compte.save(force_insert=True)
            
            # Update related LigneEcriture
            LigneEcriture.objects.filter(compte=old_compte).update(compte=new_compte)
            
            # Update children (parent relation)
            CompteComptable.objects.filter(parent=old_compte).update(parent=new_compte)
            
            # Finally, delete old account
            old_compte.delete()
            
            updated_count += 1
            
    print(f"ORM Update successful! {updated_count} accounts migrated.")

if __name__ == "__main__":
    update_via_orm()
