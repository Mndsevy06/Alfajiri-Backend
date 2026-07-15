import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.parametres.models import Succursale
from apps.plan_comptable.models import Journal, CompteComptable

def run():
    print("Populating database...")
    
    # 1. Ensure at least one Succursale exists
    succursale, created = Succursale.objects.get_or_create(
        id='sabri', 
        defaults={'label': 'Sabri', 'short': 'SAB'}
    )
    if created: print("Created Succursale: sabri")

    # 2. Ensure default journals exist
    journaux = [
        {'code': 'ACH', 'libelle': 'Achats', 'type': 'achats'},
        {'code': 'VTE', 'libelle': 'Ventes', 'type': 'ventes'},
        {'code': 'BQ', 'libelle': 'Banque', 'type': 'banque'},
        {'code': 'CAI', 'libelle': 'Caisse', 'type': 'caisse'},
        {'code': 'OD', 'libelle': 'Opérations Diverses', 'type': 'od'},
        {'code': 'FISC', 'libelle': 'Fiscalité', 'type': 'od'},
        {'code': 'RAN', 'libelle': 'A-Nouveaux', 'type': 'od'},
    ]

    for j_data in journaux:
        obj, created = Journal.objects.get_or_create(
            code=j_data['code'],
            defaults={
                'libelle': j_data['libelle'],
                'type': j_data['type'],
                'succursale': succursale,
                'dernierNumero': 0
            }
        )
        if created: print(f"Created Journal: {j_data['code']}")

    # 3. Ensure default accounts exist
    comptes = [
        {'numero': '611', 'libelle': 'Carburant', 'classe': '6', 'type': 'general'},
        {'numero': '612', 'libelle': 'Transport', 'classe': '6', 'type': 'general'},
        {'numero': '64', 'libelle': 'Frais de douane', 'classe': '6', 'type': 'general'},
        {'numero': '65', 'libelle': 'Frais de mission', 'classe': '6', 'type': 'general'},
        {'numero': '53', 'libelle': 'Caisse', 'classe': '5', 'type': 'general'},
        {'numero': '52', 'libelle': 'Banque', 'classe': '5', 'type': 'general'},
    ]

    for c_data in comptes:
        obj, created = CompteComptable.objects.get_or_create(
            numero=c_data['numero'],
            defaults=c_data
        )
        if created: print(f"Created Compte: {c_data['numero']}")

    # 4. Populating some mock Camions for Logistique
    from apps.logistique.models import Camion
    from django.utils import timezone
    
    camions_mock = [
        {
            'immat': 'IT-3456-ZA',
            'chauffeur': 'Jean Kasongo',
            'transporteur': 'Buks Haulage',
            'chargement': 32.5,
            'statut': Camion.Statut.TRANSIT_RDC,
            'progression': 80,
            'bl': 'BL-2024-001',
            'position': 'Kasumbalesa',
            'factureTransport': 3500.00,
            'douaneMontant': 1200.00,
            'dateDepart': timezone.now()
        },
        {
            'immat': 'ZA-1298-GP',
            'chauffeur': 'Paul Smith',
            'transporteur': 'Sable Transport',
            'chargement': 31.0,
            'statut': Camion.Statut.DOUANE_ZAMBIE,
            'progression': 50,
            'bl': 'BL-2024-002',
            'position': 'Chirundu',
            'factureTransport': 3200.00,
            'douaneMontant': 0.00,
            'dateDepart': timezone.now()
        },
        {
            'immat': 'CD-9988-LUS',
            'chauffeur': 'Marc Ilunga',
            'transporteur': 'Trans-Africa',
            'chargement': 34.2,
            'statut': Camion.Statut.CHARGEMENT,
            'progression': 10,
            'bl': 'BL-2024-003',
            'position': 'Ndola',
            'factureTransport': 3800.00,
            'douaneMontant': 0.00,
            'dateDepart': timezone.now()
        }
    ]
    
    for c_data in camions_mock:
        obj, created = Camion.objects.get_or_create(
            immat=c_data['immat'],
            defaults=c_data
        )
        if created: print(f"Created Camion: {c_data['immat']}")

    print("Database population complete.")

if __name__ == '__main__':
    run()
