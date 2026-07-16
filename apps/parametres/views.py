from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Dossier
from .serializers import DossierSerializer

class DossierViewSet(viewsets.ModelViewSet):
    queryset = Dossier.objects.all()
    serializer_class = DossierSerializer
    permission_classes = [IsAuthenticated]
