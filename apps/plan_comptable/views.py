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

class TiersViewSet(DossierScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Tiers.objects.all()
    serializer_class = TiersSerializer
    permission_classes = [IsAuthenticated]
