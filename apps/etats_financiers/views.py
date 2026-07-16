from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services import get_balance, get_grand_livre, get_bilan, get_compte_resultat, get_journaux_centralisation, get_tafire
from .models import CloturePeriode
from apps.saisie.models import Ecriture, LigneEcriture
from apps.rapprochement.models import LigneReleve
from apps.immobilisations.models import Immobilisation

class BalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        entite_id = request.headers.get('X-Entite-ID')
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        balance = get_balance(date_debut, date_fin, entite_id)
        return Response(balance)

class GrandLivreView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        entite_id = request.headers.get('X-Entite-ID')
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        compte_numero = request.query_params.get('compte')
        grand_livre = get_grand_livre(date_debut, date_fin, compte_numero, entite_id)
        return Response(grand_livre)

class BilanView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        entite_id = request.headers.get('X-Entite-ID')
        bilan = get_bilan(entite_id)
        return Response(bilan)

class CompteResultatView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        entite_id = request.headers.get('X-Entite-ID')
        cr = get_compte_resultat(entite_id)
        return Response(cr)

class JournauxCentralisationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        entite_id = request.headers.get('X-Entite-ID')
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        journaux = get_journaux_centralisation(date_debut, date_fin, entite_id)
        return Response(journaux)

class TafireView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        entite_id = request.headers.get('X-Entite-ID')
        tafire = get_tafire(entite_id)
        return Response(tafire)

class CloturePeriodeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, periode):
        entite_id = request.headers.get('X-Entite-ID')
        if not entite_id:
            return Response({
                'periode': periode,
                'centralisation_journaux': False,
                'rapprochement_bancaire': False,
                'inventaire_stocks': False,
                'amortissements_provisions': False,
                'regularisation_charges_produits': False,
                'arrete_comptes_tiers': False,
                'validation_commissaire': False,
            })
            
        cloture, _ = CloturePeriode.objects.get_or_create(periode=periode, dossier_id=entite_id)
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
        entite_id = request.headers.get('X-Entite-ID')
        if not entite_id:
            return Response({'error': 'X-Entite-ID manquant pour la modification'}, status=400)
            
        cloture, _ = CloturePeriode.objects.get_or_create(periode=periode, dossier_id=entite_id)
        
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
        entite_id = request.headers.get('X-Entite-ID')
        
        if step_id == 'centralisation_journaux':
            # Check for entries in brouillard
            qs = Ecriture.objects.filter(statut='brouillard')
            if entite_id:
                qs = qs.filter(dossier_id=entite_id)
            else:
                qs = qs.none()
            count_brouillard = qs.count()
            if count_brouillard > 0:
                return Response({
                    'status': 'error',
                    'message': f"Impossible de centraliser. Il reste {count_brouillard} écriture(s) en statut Brouillard.",
                    'recommendation': "Allez dans le module 'Saisie Comptable', vérifiez et validez définitivement ces écritures en attente."
                })
            return Response({'status': 'ok'})

        elif step_id == 'rapprochement_bancaire':
            # Check for un-reconciled lines
            qs1 = LigneReleve.objects.filter(rapprochement__isnull=True)
            qs2 = LigneEcriture.objects.filter(compte__numero__startswith='52', rapprochement__isnull=True)
            if entite_id:
                qs1 = qs1.filter(dossier_id=entite_id)
                qs2 = qs2.filter(dossier_id=entite_id)
            else:
                qs1 = qs1.none()
                qs2 = qs2.none()
            count_non_pointees = qs1.count() + qs2.count()
            if count_non_pointees > 0:
                return Response({
                    'status': 'error',
                    'message': f"Rapprochement incomplet. Il reste {count_non_pointees} ligne(s) non pointée(s).",
                    'recommendation': "Ouvrez le module 'Rapprochement Bancaire' et assurez-vous que toutes les opérations du mois sont pointées."
                })
            return Response({'status': 'ok'})

        elif step_id == 'amortissements_provisions':
            # Basic check: are there immobilisations with 0 cumulAmortissement but value > 0?
            qs3 = Immobilisation.objects.filter(cumulAmortissement=0, valeurAcquisition__gt=0)
            if entite_id:
                qs3 = qs3.filter(dossier_id=entite_id)
            else:
                qs3 = qs3.none()
            count_no_amort = qs3.count()
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
