from django.core.management.base import BaseCommand
from apps.parametres.models import Dossier

class Command(BaseCommand):
    help = 'Migrate existing Dossiers to the new 4111xx / 401xxx account structure'

    def handle(self, *args, **options):
        dossiers = Dossier.objects.all().order_by('dateDebut')
        
        client_counter = 1
        fournisseur_counter = 1
        
        for i, dossier in enumerate(dossiers):
            if i % 2 == 0:
                # Assign as Client
                dossier.compteClient = f"4111{client_counter:02d}"
                dossier.compteFournisseur = ""
                client_counter += 1
            else:
                # Assign as Fournisseur
                dossier.compteClient = ""
                dossier.compteFournisseur = f"401{fournisseur_counter:03d}"
                fournisseur_counter += 1
                
            dossier.save()
            
            from apps.plan_comptable.models import CompteComptable
            
            if dossier.compteClient:
                parent_client = CompteComptable.objects.filter(numero='411100').first()
                client_compte, created = CompteComptable.objects.get_or_create(
                    numero=dossier.compteClient,
                    defaults={
                        'libelle': f"Client - {dossier.raisonSociale}",
                        'classe': '4',
                        'type': 'auxiliaire',
                        'parent': parent_client,
                        'dossier': dossier
                    }
                )
                if not created and client_compte.parent != parent_client:
                    client_compte.parent = parent_client
                    client_compte.save()

            if dossier.compteFournisseur:
                parent_fourn = CompteComptable.objects.filter(numero='401100').first()
                fourn_compte, created = CompteComptable.objects.get_or_create(
                    numero=dossier.compteFournisseur,
                    defaults={
                        'libelle': f"Fournisseur - {dossier.raisonSociale}",
                        'classe': '4',
                        'type': 'auxiliaire',
                        'parent': parent_fourn,
                        'dossier': dossier
                    }
                )
                if not created and fourn_compte.parent != parent_fourn:
                    fourn_compte.parent = parent_fourn
                    fourn_compte.save()

            self.stdout.write(self.style.SUCCESS(f'Successfully updated dossier {dossier.raisonSociale}'))
        
        self.stdout.write(self.style.SUCCESS(f'Finished! Updated {client_counter - 1} clients and {fournisseur_counter - 1} fournisseurs.'))
