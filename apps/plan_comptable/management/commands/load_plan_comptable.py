import json
import os
from django.core.management.base import BaseCommand
from apps.plan_comptable.models import CompteComptable

class Command(BaseCommand):
    help = 'Load OHADA plan comptable from JSON file'

    def handle(self, *args, **kwargs):
        file_path = r'c:\Users\DELL\Desktop\Alphajiri\Code\Alfajiri\Docs\plan_comptable.json'
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        self.stdout.write("Chargement du plan comptable depuis le fichier JSON...")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        def process_comptes(comptes, classe_id, parent=None):
            for compte_data in comptes:
                numero = compte_data.get('numero')
                intitule = compte_data.get('intitule')
                
                # Default values for missing keys
                sens_normal = compte_data.get('sens_normal', 'aucun')
                if sens_normal not in ['debit', 'credit', 'aucun']:
                    sens_normal = 'aucun'
                    
                mouvementable = compte_data.get('mouvementable', False)
                lettrable = compte_data.get('lettrable', False)
                soumis_tva = compte_data.get('soumis_tva', False)
                analytique_obligatoire = compte_data.get('analytique_obligatoire', False)
                code_poste_etats_financiers = compte_data.get('code_poste_etats_financiers', None)
                
                compte, created = CompteComptable.objects.update_or_create(
                    numero=numero,
                    defaults={
                        'libelle': intitule,
                        'classe': str(classe_id),
                        'type': 'general',
                        'parent': parent,
                        'sens_normal': sens_normal,
                        'mouvementable': mouvementable,
                        'lettrable': lettrable,
                        'lettable': lettrable,
                        'soumis_tva': soumis_tva,
                        'analytique_obligatoire': analytique_obligatoire,
                        'code_poste_etats_financiers': code_poste_etats_financiers
                    }
                )
                
                if 'comptes' in compte_data:
                    process_comptes(compte_data['comptes'], classe_id, parent=compte)
        
        for classe_data in data.get('classes', []):
            classe_numero = str(classe_data.get('numero'))
            classe_intitule = classe_data.get('intitule')
            
            # Create the class as a root CompteComptable
            classe_compte, created = CompteComptable.objects.update_or_create(
                numero=classe_numero,
                defaults={
                    'libelle': classe_intitule,
                    'classe': classe_numero,
                    'type': 'general',
                    'parent': None
                }
            )
            
            if 'comptes' in classe_data:
                process_comptes(classe_data['comptes'], classe_numero, parent=classe_compte)

        self.stdout.write(self.style.SUCCESS("Plan comptable OHADA chargé avec succès en base de données !"))
