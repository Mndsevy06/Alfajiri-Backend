import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from apps.rh.serializers import BulletinPaieSerializer

data = {
    'employe': 'EMP8160',
    'periode': '2026-07',
    'jours_travailles': 26,
    'mode_paiement': 'virement',
    'salaire_base': 1000,
    'heures_sup': 0,
    'primes': [],
    'cnss_employe': 50,
    'ipr': 10,
    'avances': 0,
    'cnss_patronal': 130,
    'inpp_patronal': 10,
    'onem_patronal': 2,
    'net_a_payer': 940,
    'statut': 'validé'
}

ser = BulletinPaieSerializer(data=data)
if not ser.is_valid():
    err = json.dumps(ser.errors, separators=(',', ':'))
    print(f'Length: {len(err)}, Error: {err}')
else:
    print('Valid')
