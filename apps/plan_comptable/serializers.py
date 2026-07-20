import base64
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers
from .models import Journal, CompteComptable, Tiers

class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,') 
            ext = format.split('/')[-1] 
            id = uuid.uuid4()
            data = ContentFile(base64.b64decode(imgstr), name=str(id) + '.' + ext)
        elif isinstance(data, str) and data.startswith('http'):
            # If it's already a URL, skip updating it
            raise serializers.SkipField()
        elif isinstance(data, str) and data.startswith('/media/'):
            raise serializers.SkipField()
        return super(Base64ImageField, self).to_internal_value(data)

class JournalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Journal
        fields = '__all__'

class CompteComptableSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompteComptable
        fields = '__all__'

class TiersSerializer(serializers.ModelSerializer):
    photo_profil = Base64ImageField(max_length=None, use_url=True, required=False, allow_null=True)

    class Meta:
        model = Tiers
        fields = '__all__'
