import os
import django
from django.db import transaction

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

@transaction.atomic
def update_3_digits():
    from apps.plan_comptable.models import CompteComptable
    from apps.saisie.models import LigneEcriture
    
    comptes = list(CompteComptable.objects.all())
    all_numeros = {c.numero for c in comptes}
    
    updated_count = 0
    skipped_count = 0
    
    # We will update length 3 accounts
    for old_compte in comptes:
        if len(old_compte.numero) == 3:
            new_num = old_compte.numero.ljust(6, '0')
            
            if new_num in all_numeros and new_num != old_compte.numero:
                print(f"Skipping {old_compte.numero}: {new_num} already exists.")
                skipped_count += 1
                continue
                
            if new_num == old_compte.numero:
                continue
                
            # Create duplicate
            kwargs = {}
            for field in old_compte._meta.fields:
                kwargs[field.name] = getattr(old_compte, field.name)
            
            kwargs['numero'] = new_num
            new_compte = CompteComptable(**kwargs)
            new_compte.save(force_insert=True)
            
            # Update relations
            LigneEcriture.objects.filter(compte=old_compte).update(compte=new_compte)
            CompteComptable.objects.filter(parent=old_compte).update(parent=new_compte)
            
            # Delete old
            old_compte.delete()
            
            # Add new to our set to prevent future collisions in this loop
            all_numeros.add(new_num)
            
            updated_count += 1
            
    print(f"Update 3-digits successful! {updated_count} accounts migrated. {skipped_count} skipped due to conflicts.")

if __name__ == "__main__":
    update_3_digits()
