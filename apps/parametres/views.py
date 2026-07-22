from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Dossier
from .serializers import DossierSerializer

class DossierViewSet(viewsets.ModelViewSet):
    serializer_class = DossierSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'Super Admin':
            return Dossier.objects.all()
        return user.dossiers.all()
