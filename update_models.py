import os

apps_dir = r'c:\Users\DELL\Desktop\Alphajiri\Code\Alfajiri\Backend\apps'
apps_to_update = [
    'audit', 'etats_financiers', 'fiscalite', 'immobilisations', 
    'logistique', 'paiements', 'rapprochement', 'rh', 'saisie', 'terrain', 'ventes'
]

field_def = "    dossier = models.ForeignKey('parametres.Dossier', on_delete=models.CASCADE, null=True, blank=True, related_name='%(class)s_dossier')\n"

for app in apps_to_update:
    models_path = os.path.join(apps_dir, app, 'models.py')
    if os.path.exists(models_path):
        with open(models_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        new_lines = []
        for line in lines:
            new_lines.append(line)
            if line.startswith('class ') and '(models.Model):' in line:
                new_lines.append(field_def)
                
        with open(models_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f'Updated {app}/models.py')
