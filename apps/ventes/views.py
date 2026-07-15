from rest_framework import viewsets
from django.utils import timezone
from .models import Facture
from .serializers import FactureSerializer, FactureReadSerializer

class FactureViewSet(viewsets.ModelViewSet):
    queryset = Facture.objects.all().order_by('-date', '-numero')
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return FactureReadSerializer
        return FactureSerializer
        
    def perform_create(self, serializer):
        # Generate factures numero: FAC-VTE-YYYY-XXXX
        current_year = timezone.now().year
        count = Facture.objects.filter(date__year=current_year).count() + 1
        numero = f"FAC-VTE-{current_year}-{count:04d}"
        serializer.save(numero=numero)
