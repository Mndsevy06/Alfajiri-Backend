from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CircuitLogistiqueViewSet, EtapeCircuitViewSet, ExpeditionViewSet

router = DefaultRouter()
router.register(r'circuits', CircuitLogistiqueViewSet, basename='circuit')
router.register(r'etapes', EtapeCircuitViewSet, basename='etape')
router.register(r'expeditions', ExpeditionViewSet, basename='expedition')

urlpatterns = [
    path('', include(router.urls)),
]
