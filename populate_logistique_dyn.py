import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.logistique.models import CircuitLogistique, EtapeCircuit, Expedition
from django.utils import timezone

def run():
    print("Populating dynamic logistics...")
    
    # Create Circuit
    circuit, created = CircuitLogistique.objects.get_or_create(
        nom="Import Zambie -> RDC",
        defaults={'description': 'Route classique d\'importation transfrontalière'}
    )
    
    if created:
        # Create Steps
        etapes = [
            {'nom': 'Chargement', 'ordre': 1, 'couleur_badge': 'bg-muted text-muted-foreground', 'est_finale': False},
            {'nom': 'Transit Zambie', 'ordre': 2, 'couleur_badge': 'bg-primary/10 text-primary', 'est_finale': False},
            {'nom': 'Douane Zambie', 'ordre': 3, 'couleur_badge': 'bg-warning/10 text-warning', 'est_finale': False},
            {'nom': 'Douane RDC', 'ordre': 4, 'couleur_badge': 'bg-warning/10 text-warning', 'est_finale': False},
            {'nom': 'Transit RDC', 'ordre': 5, 'couleur_badge': 'bg-chart-4/10 text-chart-4', 'est_finale': False},
            {'nom': 'Arrivé Sabri', 'ordre': 6, 'couleur_badge': 'bg-success/10 text-success', 'est_finale': False},
            {'nom': 'Déchargé', 'ordre': 7, 'couleur_badge': 'bg-success/10 text-success', 'est_finale': True},
        ]
        
        for e_data in etapes:
            EtapeCircuit.objects.create(circuit=circuit, **e_data)
        
        print(f"Created Circuit: {circuit.nom} with {len(etapes)} steps.")

    # Get some steps to assign
    e_douane = EtapeCircuit.objects.filter(circuit=circuit, nom='Douane Zambie').first()
    e_transit_rdc = EtapeCircuit.objects.filter(circuit=circuit, nom='Transit RDC').first()
    
    # Create Expeditions
    expeditions = [
        {
            'identifiant': 'IT-3456-ZA',
            'responsable': 'Jean Kasongo',
            'transporteur': 'Buks Haulage',
            'chargement': 32.5,
            'circuit': circuit,
            'etape_actuelle': e_transit_rdc,
            'progression': 80,
            'document_reference': 'BL-2024-001',
            'position': 'Kasumbalesa',
            'facture_transport': 3500.00,
            'frais_douane': 1200.00,
            'date_depart': timezone.now()
        },
        {
            'identifiant': 'ZA-1298-GP',
            'responsable': 'Paul Smith',
            'transporteur': 'Sable Transport',
            'chargement': 31.0,
            'circuit': circuit,
            'etape_actuelle': e_douane,
            'progression': 50,
            'document_reference': 'BL-2024-002',
            'position': 'Chirundu',
            'facture_transport': 3200.00,
            'frais_douane': 0.00,
            'date_depart': timezone.now()
        }
    ]
    
    for c_data in expeditions:
        obj, created = Expedition.objects.get_or_create(
            identifiant=c_data['identifiant'],
            defaults=c_data
        )
        if created: print(f"Created Expedition: {c_data['identifiant']}")

    print("Dynamic logistics population complete.")

if __name__ == '__main__':
    run()
