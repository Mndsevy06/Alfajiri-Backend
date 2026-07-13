from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OperationTerrainViewSet

router = DefaultRouter()
router.register(r'operations', OperationTerrainViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
