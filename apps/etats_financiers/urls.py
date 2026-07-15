from django.urls import path
from .views import BalanceView, GrandLivreView, BilanView, CompteResultatView, JournauxCentralisationView, TafireView, CloturePeriodeView, VerifyClotureStepView

urlpatterns = [
    path('balance/', BalanceView.as_view(), name='balance'),
    path('grand-livre/', GrandLivreView.as_view(), name='grand_livre'),
    path('bilan/', BilanView.as_view(), name='bilan'),
    path('compte-resultat/', CompteResultatView.as_view(), name='compte_resultat'),
    path('journaux/', JournauxCentralisationView.as_view(), name='journaux'),
    path('tafire/', TafireView.as_view(), name='tafire'),
    path('cloture/<str:periode>/', CloturePeriodeView.as_view(), name='cloture_periode'),
    path('cloture/verify/<str:step_id>/<str:periode>/', VerifyClotureStepView.as_view(), name='cloture_verify_step'),
]
