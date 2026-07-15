from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Paiement
from .serializers import PaiementSerializer

class PaiementViewSet(viewsets.ModelViewSet):
    queryset = Paiement.objects.all()
    serializer_class = PaiementSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Paiement.objects.all()
        # Optional filtering could go here, e.g. by type or date
        return queryset

