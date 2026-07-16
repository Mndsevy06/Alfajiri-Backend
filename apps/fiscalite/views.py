from core.mixins import DossierScopedViewSetMixin
from rest_framework import viewsets
from .models import DeclarationFiscale, RetenueSource
from .serializers import DeclarationFiscaleSerializer, RetenueSourceSerializer

class DeclarationFiscaleViewSet(DossierScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = DeclarationFiscale.objects.all().order_by('-date_creation')
    serializer_class = DeclarationFiscaleSerializer

class RetenueSourceViewSet(DossierScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = RetenueSource.objects.all().order_by('-date_creation')
    serializer_class = RetenueSourceSerializer
