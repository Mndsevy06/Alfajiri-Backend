from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, RolePermissionViewSet

router = DefaultRouter()
router.register(r'permissions', RolePermissionViewSet, basename='permission')
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]
