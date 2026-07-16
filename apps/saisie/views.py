from core.mixins import DossierScopedViewSetMixin
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Ecriture
from .serializers import EcritureSerializer

class EcritureViewSet(DossierScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Ecriture.objects.all().order_by('-date')
    serializer_class = EcritureSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        statut = self.request.query_params.get('statut', None)
        if statut is not None:
            queryset = queryset.filter(statut=statut)
        return queryset
