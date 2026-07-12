from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EcritureViewSet

router = DefaultRouter()
router.register(r'ecritures', EcritureViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
