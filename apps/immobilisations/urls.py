from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ImmobilisationViewSet

router = DefaultRouter()
router.register(r'immobilisations', ImmobilisationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
