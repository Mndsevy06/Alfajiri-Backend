from rest_framework import serializers
from .models import Immobilisation
from apps.parametres.models import Succursale

class SiteSlugRelatedField(serializers.SlugRelatedField):
    def to_internal_value(self, data):
        try:
            obj, created = self.get_queryset().get_or_create(
                id=data.lower().replace(" ", "_"),
                defaults={'label': data, 'short': data[:3].upper()}
            )
            return obj
        except Exception:
            self.fail('invalid')

class ImmobilisationSerializer(serializers.ModelSerializer):
    site = SiteSlugRelatedField(
        slug_field='id',
        queryset=Succursale.objects.all(),
        source='succursale'
    )

    class Meta:
        model = Immobilisation
        fields = [
            'id', 'code', 'libelle', 'categorie', 'dateAcquisition',
            'valeurAcquisition', 'duree', 'methode', 'cumulAmortissement',
            'vnc', 'dotationAnnuelle', 'site'
        ]
