from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContratViewSet, BulletinPaieViewSet

router = DefaultRouter()
router.register(r'contrats', ContratViewSet)
router.register(r'bulletins', BulletinPaieViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
