from core.mixins import DossierScopedViewSetMixin
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import OperationTerrain
from .serializers import OperationTerrainSerializer

class OperationTerrainViewSet(DossierScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = OperationTerrain.objects.all()
    serializer_class = OperationTerrainSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['statut', 'type_op']
