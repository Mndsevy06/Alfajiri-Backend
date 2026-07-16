import os

models_path = r'c:\Users\DELL\Desktop\Alphajiri\Code\Alfajiri\Backend\apps\plan_comptable\models.py'
field_def = "    dossier = models.ForeignKey('parametres.Dossier', on_delete=models.CASCADE, null=True, blank=True, related_name='%(class)s_dossier')\n"

with open(models_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
new_lines = []
for line in lines:
    new_lines.append(line)
    if line.startswith('class ') and '(models.Model):' in line:
        new_lines.append(field_def)
        
with open(models_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Updated plan_comptable/models.py')
