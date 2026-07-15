from django.urls import path
from .views import LigneReleveView, LigneComptaView, ImportReleveView, LettrageManuelView, LettrageAutoView, GenererODView

urlpatterns = [
    path('releve/', LigneReleveView.as_view(), name='rapprochement-releve'),
    path('compta/', LigneComptaView.as_view(), name='rapprochement-compta'),
    path('import/', ImportReleveView.as_view(), name='rapprochement-import'),
    path('lettrer/', LettrageManuelView.as_view(), name='rapprochement-lettrer'),
    path('lettrage-auto/', LettrageAutoView.as_view(), name='rapprochement-lettrage-auto'),
    path('generer-od/', GenererODView.as_view(), name='rapprochement-generer-od'),
]
