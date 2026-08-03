from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Journal, CompteComptable, Tiers
from .serializers import JournalSerializer, CompteComptableSerializer, TiersSerializer
from core.mixins import DossierScopedViewSetMixin
from django.db.models import Q

class JournalViewSet(DossierScopedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Journal.objects.all()
    serializer_class = JournalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super(DossierScopedViewSetMixin, self).get_queryset()
        entite_id = self.request.headers.get('X-Entite-ID')
        
        if entite_id:
            queryset = queryset.filter(Q(dossier_id=entite_id) | Q(dossier__isnull=True))
        else:
            queryset = queryset.filter(dossier__isnull=True)
        return queryset

class CompteComptableViewSet(DossierScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = CompteComptable.objects.all()
    serializer_class = CompteComptableSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super(DossierScopedViewSetMixin, self).get_queryset()
        entite_id = self.request.headers.get('X-Entite-ID')
        
        if entite_id:
            # Plan Comptable Logic: Base accounts are shared (dossier_id is null). 
            # Auxiliary accounts are specific to entite_id.
            queryset = queryset.filter(Q(dossier_id=entite_id) | Q(dossier__isnull=True))
        else:
            # If no entite_id, only return base accounts
            queryset = queryset.filter(dossier__isnull=True)
        return queryset

    def list(self, request, *args, **kwargs):
        from rest_framework.response import Response
        from django.db.models import Sum
        from apps.saisie.models import LigneEcriture
        
        queryset = self.filter_queryset(self.get_queryset())
        entite_id = request.headers.get('X-Entite-ID')
        
        if entite_id:
            lignes = LigneEcriture.objects.filter(dossier_id=entite_id)
        else:
            lignes = LigneEcriture.objects.filter(dossier__isnull=True)
            
        line_sums = lignes.values('compte_id').annotate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit')
        )
        
        balance_map = {
            item['compte_id']: {
                'debit': item['total_debit'] or 0, 
                'credit': item['total_credit'] or 0
            } for item in line_sums
        }
        
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        
        account_dict = {}
        for acc in data:
            acc['soldeDebit'] = float(balance_map.get(acc['numero'], {}).get('debit', 0))
            acc['soldeCredit'] = float(balance_map.get(acc['numero'], {}).get('credit', 0))
            acc['temp_children'] = []
            account_dict[acc['numero']] = acc
            
        roots = []
        for acc in data:
            if acc['parent'] and acc['parent'] in account_dict:
                account_dict[acc['parent']]['temp_children'].append(acc)
            else:
                roots.append(acc)
                
        def aggregate_balances(node):
            debit = node['soldeDebit']
            credit = node['soldeCredit']
            for child in node['temp_children']:
                c_deb, c_cred = aggregate_balances(child)
                debit += c_deb
                credit += c_cred
            node['soldeDebit'] = debit
            node['soldeCredit'] = credit
            return debit, credit
            
        for root in roots:
            aggregate_balances(root)
            
        for acc in data:
            acc.pop('temp_children', None)
            
        return Response(data)

class TiersViewSet(DossierScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Tiers.objects.all()
    serializer_class = TiersSerializer
    permission_classes = [IsAuthenticated]

    def _handle_compte_tiers(self, tiers):
        from .models import CompteComptable
        
        # If an account is already assigned, just ensure it links back to this Tiers
        if tiers.compte:
            compte = CompteComptable.objects.filter(numero=tiers.compte).first()
            if compte and compte.tiers != tiers:
                compte.tiers = tiers
                compte.save()
            return

        # Auto-generate account based on type
        prefixes = {
            'client': '4111',
            'fournisseur': '401',
            'personnel': '422',
            'etat': '44',
            'associe': '462',
        }
        parent_prefixes = {
            'client': '411100',
            'fournisseur': '401100',
            'personnel': '422000',
            'etat': '440000',
            'associe': '462000',
        }
        prefix = prefixes.get(tiers.type, '4111')
        parent_prefix = parent_prefixes.get(tiers.type, '411100')
        
        # Generate sequential account number if it's not explicitly set to a valid one
        compte_numero = tiers.compte
        if not compte_numero or len(compte_numero) < 6:
            from django.db.models import Max
            max_compte = CompteComptable.objects.filter(
                numero__startswith=prefix, 
                type='auxiliaire'
            ).aggregate(Max('numero'))['numero__max']
            
            if max_compte and len(max_compte) >= len(prefix) + 1:
                try:
                    # Extract the suffix and increment
                    aux = int(max_compte[len(prefix):]) + 1
                    # determine padding based on how many digits are needed to reach 6 total
                    pad = 6 - len(prefix)
                    if pad < 2: pad = 2 # at least 2 digits
                    compte_numero = f"{prefix}{aux:0{pad}d}"
                except ValueError:
                    pad = max(6 - len(prefix), 2)
                    compte_numero = f"{prefix}{1:0{pad}d}"
            else:
                pad = max(6 - len(prefix), 2)
                compte_numero = f"{prefix}{1:0{pad}d}"

        if not CompteComptable.objects.filter(numero=compte_numero, dossier=tiers.dossier).exists():
            parent_compte = CompteComptable.objects.filter(numero=parent_prefix).first()
            CompteComptable.objects.create(
                numero=compte_numero,
                libelle=f"{tiers.nom}",
                classe='4',
                type='auxiliaire',
                parent=parent_compte,
                tiers=tiers,
                dossier=tiers.dossier
            )
        
        tiers.compte = compte_numero
        tiers.save(update_fields=['compte'])

    def perform_create(self, serializer):
        super().perform_create(serializer)
        tiers = serializer.instance
        self._handle_compte_tiers(tiers)

    def perform_update(self, serializer):
        super().perform_update(serializer)
        tiers = serializer.instance
        self._handle_compte_tiers(tiers)
