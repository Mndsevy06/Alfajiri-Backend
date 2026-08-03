import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.plan_comptable.models import CompteComptable

related_objects = [
    f.related_model for f in CompteComptable._meta.get_fields()
    if (f.one_to_many or f.one_to_one) and f.auto_created and not f.concrete
]
print("Related Models:")
for rel in related_objects:
    print(rel)
