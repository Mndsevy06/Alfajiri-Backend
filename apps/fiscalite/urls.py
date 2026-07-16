from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DeclarationFiscaleViewSet, RetenueSourceViewSet

router = DefaultRouter()
router.register(r'declarations', DeclarationFiscaleViewSet)
router.register(r'retenues', RetenueSourceViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
