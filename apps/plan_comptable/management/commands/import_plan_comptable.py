import os
import pandas as pd
from django.core.management.base import BaseCommand
from apps.plan_comptable.models import CompteComptable

class Command(BaseCommand):
    help = 'Import plan comptable from Excel file'

    def handle(self, *args, **options):
        # 1. Read Excel file
        file_path = r'c:\Users\DELL\Desktop\Alphajiri\Code\Alfajiri\Update\PLAN COMPTABLE  TRANSLOG AFRICA_085810.xlsx'
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading Excel file: {e}"))
            return

        # Expected columns: COMPTE, INTITULE DU COMPTE, CODE AFS
        # 2. Iterate and update_or_create
        created_count = 0
        updated_count = 0
        
        accounts_data = []
        for index, row in df.iterrows():
            compte = str(row['COMPTE']).strip()
            # Supprimer les éventuels '.0' si lu comme float
            if compte.endswith('.0'):
                compte = compte[:-2]
            
            if not compte or compte == 'nan':
                continue
                
            intitule = str(row['INTITULE DU COMPTE']).strip()
            code_afs = str(row['CODE AFS']).strip()
            if code_afs == 'nan':
                code_afs = None
                
            classe = compte[0] if len(compte) > 0 else '0'
            
            accounts_data.append({
                'numero': compte,
                'libelle': intitule,
                'code_poste_etats_financiers': code_afs,
                'classe': classe,
            })
            
        self.stdout.write(f"Found {len(accounts_data)} accounts in Excel.")
        
        # First pass: Create/Update
        for data in accounts_data:
            obj, created = CompteComptable.objects.update_or_create(
                numero=data['numero'],
                defaults={
                    'libelle': data['libelle'],
                    'code_poste_etats_financiers': data['code_poste_etats_financiers'],
                    'classe': data['classe'],
                    'type': 'general',
                    'dossier': None
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1
                
        self.stdout.write(self.style.SUCCESS(f"Pass 1 complete: {created_count} created, {updated_count} updated."))
        
        # Second pass: Assign parents to restructure all accounts including Compte 42
        # For all accounts, find the longest existing prefix and set as parent
        all_accounts = CompteComptable.objects.filter(dossier__isnull=True).order_by('numero')
        # load into memory for fast lookup
        account_nums = set(all_accounts.values_list('numero', flat=True))
        
        parent_updated = 0
        for acc in all_accounts:
            numero = acc.numero
            # Try to find a parent by progressively removing the last character
            parent_num = None
            for i in range(len(numero) - 1, 0, -1):
                candidate = numero[:i]
                if candidate in account_nums:
                    parent_num = candidate
                    break
            
            if parent_num and acc.parent_id != parent_num:
                acc.parent_id = parent_num
                acc.save(update_fields=['parent_id'])
                parent_updated += 1
                
        self.stdout.write(self.style.SUCCESS(f"Pass 2 complete: {parent_updated} parents assigned/updated."))
        self.stdout.write(self.style.SUCCESS("Import plan comptable and restructuring (including Compte 42) completed successfully."))
