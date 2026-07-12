from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JournalViewSet, CompteComptableViewSet

router = DefaultRouter()
router.register(r'journaux', JournalViewSet)
router.register(r'comptes', CompteComptableViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
