import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def check_3_digits():
    from apps.plan_comptable.models import CompteComptable
    
    comptes = CompteComptable.objects.all().values_list('numero', flat=True)
    all_comptes = set(comptes)
    
    # We will see what happens if we pad length 2 and 3
    to_pad_3 = []
    to_pad_2 = []
    
    for numero in all_comptes:
        if len(numero) == 3:
            padded = numero.ljust(6, '0')
            to_pad_3.append((numero, padded))
        elif len(numero) == 2:
            padded = numero.ljust(6, '0')
            to_pad_2.append((numero, padded))
            
    # Check conflicts for 3 digits
    conflicts_3 = []
    for old, new in to_pad_3:
        if new in all_comptes:
            conflicts_3.append(f"Cannot pad '{old}' because '{new}' already exists.")
            
    # Check conflicts for 2 digits
    conflicts_2 = []
    for old, new in to_pad_2:
        if new in all_comptes:
            conflicts_2.append(f"Cannot pad '{old}' because '{new}' already exists.")

    print(f"--- For 3 digits (Total {len(to_pad_3)}) ---")
    if conflicts_3:
        for c in conflicts_3[:10]:
            print(c)
        if len(conflicts_3) > 10:
            print(f"... and {len(conflicts_3) - 10} more.")
    else:
        print("No conflicts for 3 digits!")
        
    print(f"\n--- For 2 digits (Total {len(to_pad_2)}) ---")
    if conflicts_2:
        for c in conflicts_2[:10]:
            print(c)
        if len(conflicts_2) > 10:
            print(f"... and {len(conflicts_2) - 10} more.")
    else:
        print("No conflicts for 2 digits!")

if __name__ == "__main__":
    check_3_digits()
