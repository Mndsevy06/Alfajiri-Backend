from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Journal, CompteComptable, Tiers
from .serializers import JournalSerializer, CompteComptableSerializer, TiersSerializer

class JournalViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Journal.objects.all()
    serializer_class = JournalSerializer
    permission_classes = [IsAuthenticated]

class CompteComptableViewSet(viewsets.ModelViewSet):
    queryset = CompteComptable.objects.all()
    serializer_class = CompteComptableSerializer
    permission_classes = [IsAuthenticated]

class TiersViewSet(viewsets.ModelViewSet):
    queryset = Tiers.objects.all()
    serializer_class = TiersSerializer
    permission_classes = [IsAuthenticated]
