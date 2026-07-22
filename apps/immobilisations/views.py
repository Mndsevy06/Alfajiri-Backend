from core.mixins import DossierScopedViewSetMixin
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Immobilisation
from .serializers import ImmobilisationSerializer

class ImmobilisationViewSet(DossierScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Immobilisation.objects.all()
    serializer_class = ImmobilisationSerializer
    def perform_create(self, serializer):
        immo = serializer.save()
        immo.calculate_current_state()
        immo.save()

    def perform_update(self, serializer):
        immo = serializer.save()
        immo.calculate_current_state()
        immo.save()

    @action(detail=False, methods=['get'])
    def sites(self, request):
        from apps.parametres.models import Succursale
        sites = Succursale.objects.all().values('id', 'label', 'short')
        return Response(list(sites))

    @action(detail=True, methods=['get'])
    def amortissement(self, request, pk=None):
        immo = self.get_object()
        plan = immo.get_amortissement_plan()
        return Response(plan)
