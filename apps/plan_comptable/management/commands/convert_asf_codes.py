import json
import os
from django.core.management.base import BaseCommand
from apps.plan_comptable.models import CompteComptable

def get_afs_code(numero):
    if not numero:
        return None
    
    # Check prefixes in descending order of length
    # 3-digit prefixes
    prefix_3 = numero[:3]
    if prefix_3 == '101': return 'CA'
    if prefix_3 == '102': return 'CA'
    if prefix_3 == '103': return 'CA'
    if prefix_3 == '104': return 'CA'
    if prefix_3 == '105': return 'CA'
    if prefix_3 == '106': return 'CE'
    if prefix_3 == '245': return 'AN'
    if prefix_3 == '401': return 'DJ'
    if prefix_3 == '402': return 'DJ'
    if prefix_3 == '408': return 'DJ'
    if prefix_3 == '409': return 'BH'
    if prefix_3 == '411': return 'BI'
    if prefix_3 == '412': return 'BI'
    if prefix_3 == '414': return 'BI'
    if prefix_3 == '415': return 'BI'
    if prefix_3 == '416': return 'BI'
    if prefix_3 == '418': return 'BI'
    if prefix_3 == '419': return 'DI'
    if prefix_3 == '601': return 'RA'
    if prefix_3 == '602': return 'RA'
    if prefix_3 == '603': return 'RB'
    if prefix_3 == '604': return 'RE'
    if prefix_3 == '605': return 'RE'
    if prefix_3 == '608': return 'RE'
    if prefix_3 == '651': return 'RI'
    if prefix_3 == '664': return 'RK'
    if prefix_3 == '701': return 'TA'
    if prefix_3 == '702': return 'TA'
    if prefix_3 == '703': return 'TA'
    if prefix_3 == '704': return 'TA'
    if prefix_3 == '705': return 'TA'
    if prefix_3 == '706': return 'TA'
    if prefix_3 == '707': return 'TD'
    if prefix_3 == '776': return 'TK'
    
    # 2-digit prefixes
    prefix_2 = numero[:2]
    if prefix_2 == '11': return 'CF'
    if prefix_2 == '12': return 'CH'
    if prefix_2 == '13': return 'CI'
    if prefix_2 == '14': return 'CF'
    if prefix_2 == '15': return 'DF'
    if prefix_2 == '16': return 'DA'
    if prefix_2 == '17': return 'DA'
    if prefix_2 == '18': return 'DA'
    if prefix_2 == '19': return 'DA'
    if prefix_2 == '21': return 'AM'
    if prefix_2 == '22': return 'AM'
    if prefix_2 == '23': return 'AM'
    if prefix_2 == '24': return 'AM'
    if prefix_2 == '25': return 'AS'
    if prefix_2 == '26': return 'AS'
    if prefix_2 == '27': return 'AS'
    if prefix_2 == '31': return 'BB'
    if prefix_2 == '32': return 'BB'
    if prefix_2 == '33': return 'BB'
    if prefix_2 == '34': return 'BB'
    if prefix_2 == '35': return 'BB'
    if prefix_2 == '36': return 'BB'
    if prefix_2 == '37': return 'BB'
    if prefix_2 == '38': return 'BB'
    if prefix_2 == '42': return 'DK'
    if prefix_2 == '43': return 'DK'
    if prefix_2 == '44': return 'DK'
    if prefix_2 == '45': return 'DK'
    if prefix_2 == '46': return 'DK'
    if prefix_2 == '47': return 'DK'
    if prefix_2 == '48': return 'DH'
    if prefix_2 == '52': return 'BS'
    if prefix_2 == '53': return 'BS'
    if prefix_2 == '54': return 'BS'
    if prefix_2 == '55': return 'BS'
    if prefix_2 == '56': return 'DQ'
    if prefix_2 == '57': return 'BS'
    if prefix_2 == '58': return 'BS'
    if prefix_2 == '61': return 'RG'
    if prefix_2 == '62': return 'RH'
    if prefix_2 == '63': return 'RH'
    if prefix_2 == '64': return 'RI'
    if prefix_2 == '65': return 'RJ'
    if prefix_2 == '66': return 'RJ'
    if prefix_2 == '67': return 'RM'
    if prefix_2 == '68': return 'RM'
    if prefix_2 == '69': return 'RM'
    if prefix_2 == '75': return 'TH'
    if prefix_2 == '76': return 'TK'
    if prefix_2 == '77': return 'TH'
    if prefix_2 == '78': return 'TK'
    if prefix_2 == '79': return 'TD'
    if prefix_2 == '81': return 'RO'
    if prefix_2 == '82': return 'TN'
    if prefix_2 == '83': return 'RP'
    if prefix_2 == '84': return 'TO'
    if prefix_2 == '89': return 'RS'

    # 1-digit prefixes
    prefix_1 = numero[0]
    if prefix_1 == '1': return 'CF'
    if prefix_1 == '2': return 'AM'
    if prefix_1 == '3': return 'BB'
    if prefix_1 == '4': return 'DK'
    if prefix_1 == '5': return 'BS'
    if prefix_1 == '6': return 'RJ'
    if prefix_1 == '7': return 'TH'
    if prefix_1 == '8': return 'RO'
    if prefix_1 == '9': return 'EHB'
    
    return None

class Command(BaseCommand):
    help = 'Convert code_poste_etats_financiers from descriptive phrases to short AFS codes in both DB and JSON file'

    def handle(self, *args, **kwargs):
        # 1. Update JSON file
        json_path = r'c:\Users\DELL\Desktop\Alphajiri\Code\Alfajiri\Docs\plan_comptable.json'
        if os.path.exists(json_path):
            self.stdout.write(f"Updating JSON file at {json_path}...")
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            def process_compte(c):
                num = c.get('numero', '')
                if num:
                    c['code_poste_etats_financiers'] = get_afs_code(num)
                if 'comptes' in c:
                    for sub_c in c['comptes']:
                        process_compte(sub_c)

            if 'classes' in data:
                for cls in data['classes']:
                    if 'comptes' in cls:
                        for c in cls['comptes']:
                            process_compte(c)

            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            self.stdout.write(self.style.SUCCESS("plan_comptable.json updated successfully with short codes."))
        else:
            self.stdout.write(self.style.WARNING(f"JSON file not found at {json_path}"))

        # 2. Update Database
        self.stdout.write("Updating CompteComptable objects in database...")
        all_accounts = CompteComptable.objects.all()
        updated_db_count = 0
        for acc in all_accounts:
            code = get_afs_code(acc.numero)
            if code and acc.code_poste_etats_financiers != code:
                acc.code_poste_etats_financiers = code
                acc.save(update_fields=['code_poste_etats_financiers'])
                updated_db_count += 1

        self.stdout.write(self.style.SUCCESS(f"Database update complete: {updated_db_count} accounts updated with short codes."))
