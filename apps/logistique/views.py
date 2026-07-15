from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import CircuitLogistique, EtapeCircuit, Expedition
from .serializers import CircuitLogistiqueSerializer, EtapeCircuitSerializer, ExpeditionSerializer

class CircuitLogistiqueViewSet(viewsets.ModelViewSet):
    queryset = CircuitLogistique.objects.all()
    serializer_class = CircuitLogistiqueSerializer

class EtapeCircuitViewSet(viewsets.ModelViewSet):
    queryset = EtapeCircuit.objects.all().order_by('circuit', 'ordre')
    serializer_class = EtapeCircuitSerializer
    # allow filtering by circuit
    filterset_fields = ['circuit']

class ExpeditionViewSet(viewsets.ModelViewSet):
    queryset = Expedition.objects.all().order_by('-date_depart', 'identifiant')
    serializer_class = ExpeditionSerializer

    @action(detail=True, methods=['post'])
    def valider_passage(self, request, pk=None):
        expedition = self.get_object()
        
        # Get all steps for this circuit
        etapes = list(EtapeCircuit.objects.filter(circuit=expedition.circuit).order_by('ordre'))
        
        if not etapes:
            return Response({"detail": "Ce circuit n'a aucune étape configurée."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Determine current index
        if expedition.etape_actuelle is None:
            # Not started, move to step 1
            next_etape = etapes[0]
            current_index = -1
        else:
            try:
                # Find index of current step in the ordered list
                current_index = next(i for i, e in enumerate(etapes) if e.id == expedition.etape_actuelle.id)
                if current_index < len(etapes) - 1:
                    next_etape = etapes[current_index + 1]
                else:
                    return Response({"detail": "L'expédition a déjà atteint l'étape finale."}, status=status.HTTP_400_BAD_REQUEST)
            except StopIteration:
                return Response({"detail": "L'étape actuelle ne fait pas partie de ce circuit."}, status=status.HTTP_400_BAD_REQUEST)

        # Update expedition
        expedition.etape_actuelle = next_etape
        
        # Calculate progression
        total_etapes = len(etapes)
        new_index = current_index + 1
        expedition.progression = min(100, int(((new_index + 1) / total_etapes) * 100))
        
        if next_etape.est_finale:
            expedition.date_arrivee = timezone.now()
            
        expedition.save()
        serializer = self.get_serializer(expedition)
        return Response(serializer.data)
