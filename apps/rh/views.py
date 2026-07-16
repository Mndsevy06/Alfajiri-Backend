from core.mixins import DossierScopedViewSetMixin
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Contrat, BulletinPaie
from .serializers import ContratSerializer, BulletinPaieSerializer

class ContratViewSet(DossierScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Contrat.objects.all()
    serializer_class = ContratSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        employe = self.request.query_params.get('employe', None)
        if employe is not None:
            queryset = queryset.filter(employe=employe)
        return queryset

class BulletinPaieViewSet(DossierScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = BulletinPaie.objects.all().order_by('-periode', '-cree_le')
    serializer_class = BulletinPaieSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        print("==== BULLETIN CREATE REQUEST ====")
        print("DATA:", request.data)
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("ERRORS:", serializer.errors)
        return super().create(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        periode = self.request.query_params.get('periode', None)
        employe = self.request.query_params.get('employe', None)
        
        if periode:
            queryset = queryset.filter(periode=periode)
        if employe:
            queryset = queryset.filter(employe=employe)
            
        return queryset
