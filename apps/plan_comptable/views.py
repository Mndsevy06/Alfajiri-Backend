from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Journal, CompteComptable
from .serializers import JournalSerializer, CompteComptableSerializer

class JournalViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Journal.objects.all()
    serializer_class = JournalSerializer
    permission_classes = [IsAuthenticated]

class CompteComptableViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CompteComptable.objects.all()
    serializer_class = CompteComptableSerializer
    permission_classes = [IsAuthenticated]
