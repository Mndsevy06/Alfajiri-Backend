from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JournalViewSet, CompteComptableViewSet, TiersViewSet

router = DefaultRouter()
router.register(r'journaux', JournalViewSet)
router.register(r'comptes', CompteComptableViewSet)
router.register(r'tiers', TiersViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
