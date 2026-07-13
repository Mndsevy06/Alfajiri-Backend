import os
import sys
import django
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.plan_comptable.models import CompteComptable

json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'Docs', 'plan_comptable.json')

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

updated_count = 0

def process_compte(c):
    global updated_count
    numero = c.get('numero')
    if numero:
        try:
            compte = CompteComptable.objects.get(numero=numero)
            
            # Map JSON to Model fields
            sens = c.get('sens_normal', 'aucun')
            if sens == 'debit':
                compte.sens_normal = CompteComptable.SensNormal.DEBIT
            elif sens == 'credit':
                compte.sens_normal = CompteComptable.SensNormal.CREDIT
            else:
                compte.sens_normal = CompteComptable.SensNormal.AUCUN
                
            compte.mouvementable = c.get('mouvementable', False)
            compte.lettrable = c.get('lettrable', False)
            compte.lettable = c.get('lettrable', False)
            compte.soumis_tva = c.get('soumis_tva', False)
            compte.analytique_obligatoire = c.get('analytique_obligatoire', False)
            compte.requiert_auxiliaire = c.get('requiert_auxiliaire', False)
            
            compte.save()
            updated_count += 1
        except CompteComptable.DoesNotExist:
            pass # Ignore if not in DB yet
            
    if 'comptes' in c:
        for sub_c in c['comptes']:
            process_compte(sub_c)

if 'classes' in data:
    for cls in data['classes']:
        if 'comptes' in cls:
            for c in cls['comptes']:
                process_compte(c)

print(f"Mise à jour terminée. {updated_count} comptes modifiés.")
