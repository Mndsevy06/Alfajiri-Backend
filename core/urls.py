"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse, JsonResponse
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('favicon.ico', lambda request: HttpResponse(status=204)),
    path('', lambda request: JsonResponse({"message": "Welcome to the Alfajiri API!"})),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/paiements/', include('apps.paiements.urls')),
    path('api/plan_comptable/', include('apps.plan_comptable.urls')),
    path('api/saisie/', include('apps.saisie.urls')),
    path('api/terrain/', include('apps.terrain.urls')),
    path('api/users/', include('apps.authentification.urls')),
    path('api/etats_financiers/', include('apps.etats_financiers.urls')),
    path('api/', include('apps.immobilisations.urls')),
    path('api/rapprochement/', include('apps.rapprochement.urls')),
    path('api/logistique/', include('apps.logistique.urls')),
    path('api/ventes/', include('apps.ventes.urls')),
]
