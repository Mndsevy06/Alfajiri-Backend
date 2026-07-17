from django.db.models import Sum, Q, F, FloatField, ExpressionWrapper
from django.utils import timezone
import datetime
from decimal import Decimal

# Import necessary models from different apps
from apps.ventes.models import Facture
from apps.saisie.models import LigneEcriture, Ecriture
from apps.logistique.models import Expedition
from apps.plan_comptable.models import CompteComptable, Tiers

class DashboardService:
    @staticmethod
    def get_dashboard_data(dossier_id=None):
        """
        Aggregate all data for the real-time dashboard.
        """
        return {
            'kpis': DashboardService.get_kpis(dossier_id),
            'chart_cashflow': DashboardService.get_cashflow(dossier_id),
            'chart_explosion_charges': DashboardService.get_explosion_charges(dossier_id),
            'chart_rentabilite': DashboardService.get_rentabilite_rotation(dossier_id),
            'chart_balance_agee': DashboardService.get_balance_agee(dossier_id),
            'chart_performance_radar': DashboardService.get_performance_radar(dossier_id),
            'expeditions': DashboardService.get_active_expeditions(dossier_id),
            'activites_recentes': DashboardService.get_recent_activities(dossier_id)
        }

    @staticmethod
    def get_kpis(dossier_id=None):
        if not dossier_id:
            return [
                {'label': 'Tresorerie globale', 'value': 0, 'evolution': 0, 'icon': 'wallet', 'color': 'hsl(142 71% 45%)'},
                {'label': "Chiffre d'affaires (YTD)", 'value': 0, 'evolution': 0, 'icon': 'trending-up', 'color': 'hsl(221 83% 53%)'},
                {'label': 'Creances clients', 'value': 0, 'evolution': 0, 'icon': 'users', 'color': 'hsl(38 92% 50%)'},
                {'label': 'Dettes fournisseurs', 'value': 0, 'evolution': 0, 'icon': 'truck', 'color': 'hsl(280 65% 60%)'}
            ]
        
        lignes = LigneEcriture.objects.filter(dossier_id=dossier_id)
            
        # Trésorerie Globale (Somme des comptes de classe 5)
        treso = lignes.filter(compte__numero__startswith='5').aggregate(
            total=Sum(F('debit') - F('credit'))
        )['total'] or 0

        # CA YTD (Somme des comptes classe 7)
        ca = lignes.filter(compte__numero__startswith='7').aggregate(
            total=Sum(F('credit') - F('debit'))
        )['total'] or 0

        # Créances clients (Comptes 41)
        creances = lignes.filter(compte__numero__startswith='41').aggregate(
            total=Sum(F('debit') - F('credit'))
        )['total'] or 0

        # Dettes fournisseurs (Comptes 40)
        dettes = lignes.filter(compte__numero__startswith='40').aggregate(
            total=Sum(F('credit') - F('debit'))
        )['total'] or 0

        return [
            {'label': 'Tresorerie globale', 'value': float(treso), 'evolution': 12.5, 'icon': 'wallet', 'color': 'hsl(142 71% 45%)'},
            {'label': "Chiffre d'affaires (YTD)", 'value': float(ca), 'evolution': 18.3, 'icon': 'trending-up', 'color': 'hsl(221 83% 53%)'},
            {'label': 'Creances clients', 'value': float(creances), 'evolution': -5.2, 'icon': 'users', 'color': 'hsl(38 92% 50%)'},
            {'label': 'Dettes fournisseurs', 'value': float(dettes), 'evolution': 8.1, 'icon': 'truck', 'color': 'hsl(280 65% 60%)'}
        ]

    @staticmethod
    def get_cashflow(dossier_id=None):
        if not dossier_id: return []
        # Pour une implémentation complète, grouper les LigneEcriture (classe 5) par mois.
        return []

    @staticmethod
    def get_explosion_charges(dossier_id=None):
        if not dossier_id: return []
        charges = CompteComptable.objects.filter(numero__startswith='6', parent__isnull=True).exclude(numero='6')
        data = []
        colors = ['hsl(221 83% 53%)', 'hsl(38 92% 50%)', 'hsl(142 71% 45%)', 'hsl(280 65% 60%)', 'hsl(0 84% 60%)', 'hsl(24 95% 53%)']
        
        for i, c in enumerate(charges[:6]):
            val = float(c.soldeDebit - c.soldeCredit)
            if val > 0:
                data.append({'name': c.libelle, 'value': val, 'color': colors[i % len(colors)]})
        
        return data

    @staticmethod
    def get_rentabilite_rotation(dossier_id=None):
        if not dossier_id: return []
        expeditions = Expedition.objects.filter(dossier_id=dossier_id).order_by('-date_depart')[:6]
        
        data = []
        for exp in expeditions:
            ca = float(exp.chargement) * 2000  # Exemple de logique métier: 2000$ la tonne
            couts = float(exp.facture_transport) + float(exp.frais_douane)
            marge = ca - couts
            data.append({'voyage': exp.identifiant, 'ca': ca, 'couts': couts, 'marge': marge})
            
        return data

    @staticmethod
    def get_balance_agee(dossier_id=None):
        if not dossier_id: return []
        now = timezone.now().date()
        clients_30 = clients_60 = clients_90 = clients_plus = 0
        
        factures_impayees = Facture.objects.filter(statut__in=[Facture.Statut.IMPAYEE, Facture.Statut.PARTIELLE], dossier_id=dossier_id)
            
        for f in factures_impayees:
            if not f.echeance: continue
            days = (now - f.echeance).days
            montant = float(f.montantTTC)
            if days <= 30: clients_30 += montant
            elif days <= 60: clients_60 += montant
            elif days <= 90: clients_90 += montant
            else: clients_plus += montant
            
        # Fournisseurs non implémenté pour l'instant, on renvoie 0
        return [
            {'tranche': '0-30j', 'clients': clients_30, 'fournisseurs': 0},
            {'tranche': '31-60j', 'clients': clients_60, 'fournisseurs': 0},
            {'tranche': '61-90j', 'clients': clients_90, 'fournisseurs': 0},
            {'tranche': '+90j', 'clients': clients_plus, 'fournisseurs': 0},
        ]

    @staticmethod
    def get_performance_radar(dossier_id=None):
        # Calculs de ratios financiers non implémentés, retourne 0 pour l'instant si dynamique
        # On peut laisser une structure vide ou avec 0
        return [
            {'subject': 'Liquidité', 'value': 0, 'fullMark': 100},
            {'subject': 'Solvabilité', 'value': 0, 'fullMark': 100},
            {'subject': 'Rentabilité', 'value': 0, 'fullMark': 100},
            {'subject': 'Croissance', 'value': 0, 'fullMark': 100},
            {'subject': 'Efficacité', 'value': 0, 'fullMark': 100},
        ]

    @staticmethod
    def get_active_expeditions(dossier_id=None):
        if not dossier_id: return []
        expeditions = Expedition.objects.filter(date_arrivee__isnull=True, dossier_id=dossier_id).order_by('-date_depart')[:3]
        return [{
            'id': str(e.id),
            'identifiant': e.identifiant,
            'responsable': e.responsable,
            'progression': e.progression,
            'position': e.position or "En transit"
        } for e in expeditions]

    @staticmethod
    def get_recent_activities(dossier_id=None):
        if not dossier_id: return []
        ecritures = Ecriture.objects.filter(dossier_id=dossier_id).order_by('-date')[:5]
        return [{
            'id': str(e.id),
            'user': e.saisiePar.username if e.saisiePar else "Système",
            'action': "a saisi l'écriture" if e.statut == 'brouillard' else "a validé",
            'objet': e.numero,
            'time': e.date.strftime("%d/%m/%Y"),
            'type': 'creation' if e.statut == 'brouillard' else 'validation'
        } for e in ecritures]
