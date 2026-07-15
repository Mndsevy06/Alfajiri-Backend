from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services import get_balance, get_grand_livre, get_bilan, get_compte_resultat, get_journaux_centralisation, get_tafire
from .models import CloturePeriode
from apps.saisie.models import Ecriture
from apps.rapprochement.models import LigneReleve, LigneCompta
from apps.immobilisations.models import Immobilisation

class BalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        balance = get_balance(date_debut, date_fin)
        return Response(balance)

class GrandLivreView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        compte_numero = request.query_params.get('compte')
        grand_livre = get_grand_livre(date_debut, date_fin, compte_numero)
        return Response(grand_livre)

class BilanView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bilan = get_bilan()
        return Response(bilan)

class CompteResultatView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cr = get_compte_resultat()
        return Response(cr)

class JournauxCentralisationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        journaux = get_journaux_centralisation(date_debut, date_fin)
        return Response(journaux)

class TafireView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tafire = get_tafire()
        return Response(tafire)

class CloturePeriodeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, periode):
        cloture, _ = CloturePeriode.objects.get_or_create(periode=periode)
        data = {
            'periode': cloture.periode,
            'centralisation_journaux': cloture.centralisation_journaux,
            'rapprochement_bancaire': cloture.rapprochement_bancaire,
            'inventaire_stocks': cloture.inventaire_stocks,
            'amortissements_provisions': cloture.amortissements_provisions,
            'regularisation_charges_produits': cloture.regularisation_charges_produits,
            'arrete_comptes_tiers': cloture.arrete_comptes_tiers,
            'validation_commissaire': cloture.validation_commissaire,
        }
        return Response(data)

    def put(self, request, periode):
        cloture, _ = CloturePeriode.objects.get_or_create(periode=periode)
        
        field = request.data.get('field')
        value = request.data.get('value')
        
        if field and hasattr(cloture, field):
            setattr(cloture, field, value)
            cloture.save()
            
        data = {
            'periode': cloture.periode,
            'centralisation_journaux': cloture.centralisation_journaux,
            'rapprochement_bancaire': cloture.rapprochement_bancaire,
            'inventaire_stocks': cloture.inventaire_stocks,
            'amortissements_provisions': cloture.amortissements_provisions,
            'regularisation_charges_produits': cloture.regularisation_charges_produits,
            'arrete_comptes_tiers': cloture.arrete_comptes_tiers,
            'validation_commissaire': cloture.validation_commissaire,
        }
        return Response(data)

class VerifyClotureStepView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, step_id, periode):
        if step_id == 'centralisation_journaux':
            # Check for entries in brouillard
            count_brouillard = Ecriture.objects.filter(statut='brouillard').count()
            if count_brouillard > 0:
                return Response({
                    'status': 'error',
                    'message': f"Impossible de centraliser. Il reste {count_brouillard} écriture(s) en statut Brouillard.",
                    'recommendation': "Allez dans le module 'Saisie Comptable', vérifiez et validez définitivement ces écritures en attente."
                })
            return Response({'status': 'ok'})

        elif step_id == 'rapprochement_bancaire':
            # Check for un-reconciled lines
            count_non_pointees = LigneReleve.objects.filter(pointe=False).count() + LigneCompta.objects.filter(pointe=False).count()
            if count_non_pointees > 0:
                return Response({
                    'status': 'error',
                    'message': f"Rapprochement incomplet. Il reste {count_non_pointees} ligne(s) non pointée(s).",
                    'recommendation': "Ouvrez le module 'Rapprochement Bancaire' et assurez-vous que toutes les opérations du mois sont pointées."
                })
            return Response({'status': 'ok'})

        elif step_id == 'amortissements_provisions':
            # Basic check: are there immobilisations with 0 cumulAmortissement but value > 0?
            count_no_amort = Immobilisation.objects.filter(cumulAmortissement=0, valeurAcquisition__gt=0).count()
            if count_no_amort > 0:
                return Response({
                    'status': 'error',
                    'message': f"Des amortissements semblent manquants pour {count_no_amort} immobilisation(s).",
                    'recommendation': "Vérifiez le module 'Immobilisations' et générez les dotations aux amortissements si nécessaire."
                })
            return Response({'status': 'ok'})

        # Manual steps: return OK automatically
        elif step_id in ['inventaire_stocks', 'regularisation_charges_produits', 'arrete_comptes_tiers', 'validation_commissaire']:
            return Response({'status': 'ok'})

        return Response({'status': 'error', 'message': 'Étape inconnue', 'recommendation': ''})
