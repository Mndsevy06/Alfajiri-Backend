import os

apps_dir = r'c:\Users\DELL\Desktop\Alphajiri\Code\Alfajiri\Backend\apps'
apps_to_update = [
    'audit', 'etats_financiers', 'fiscalite', 'immobilisations', 
    'logistique', 'paiements', 'rapprochement', 'rh', 'saisie', 'terrain', 'ventes'
]

for app in apps_to_update:
    views_path = os.path.join(apps_dir, app, 'views.py')
    if os.path.exists(views_path):
        with open(views_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        has_mixin_import = any('DossierScopedViewSetMixin' in line for line in lines)
        
        if not has_mixin_import:
            new_lines = []
            imports_done = False
            for line in lines:
                if line.startswith('class ') and 'ViewSet(' in line:
                    if not imports_done:
                        new_lines.insert(0, "from core.mixins import DossierScopedViewSetMixin\n")
                        imports_done = True
                    # Replace viewsets.ModelViewSet with DossierScopedViewSetMixin, viewsets.ModelViewSet
                    line = line.replace('viewsets.ModelViewSet', 'DossierScopedViewSetMixin, viewsets.ModelViewSet')
                new_lines.append(line)
                
            with open(views_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f'Updated {app}/views.py')
