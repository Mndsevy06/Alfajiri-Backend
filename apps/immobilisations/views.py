from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Immobilisation
from .serializers import ImmobilisationSerializer

class ImmobilisationViewSet(viewsets.ModelViewSet):
    queryset = Immobilisation.objects.all()
    serializer_class = ImmobilisationSerializer
    @action(detail=False, methods=['get'])
    def sites(self, request):
        from apps.parametres.models import Succursale
        sites = Succursale.objects.all().values('id', 'label', 'short')
        return Response(list(sites))

    @action(detail=True, methods=['get'])
    def amortissement(self, request, pk=None):
        immo = self.get_object()
        plan = []
        vnc = float(immo.valeurAcquisition)
        
        # Coeff dégressif simplifié, en réalité dépend des règles fiscales
        taux = 1.0 / immo.duree if immo.methode == Immobilisation.Methode.LINEAIRE else (1.0 / immo.duree) * 1.5

        cumul = 0.0
        for i in range(1, immo.duree + 1):
            if immo.methode == Immobilisation.Methode.LINEAIRE:
                # En linéaire pur, la dotation est constante basée sur la valeur d'acquisition
                dotation = float(immo.valeurAcquisition) * taux
            else:
                # En dégressif, la dotation est basée sur la VNC
                dotation = vnc * taux
                
            # Pour la dernière année, on s'assure d'amortir complètement
            if i == immo.duree and vnc < dotation:
                dotation = vnc

            base = float(immo.valeurAcquisition) if immo.methode == Immobilisation.Methode.LINEAIRE else vnc
            vnc -= dotation
            cumul += dotation

            plan.append({
                'annee': i,
                'baseAmortissable': round(base, 2),
                'dotation': round(dotation, 2),
                'cumul': round(cumul, 2),
                'vnc': round(max(vnc, 0), 2)
            })

        return Response(plan)
