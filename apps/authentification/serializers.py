from rest_framework import serializers
from .models import User, RolePermission

from apps.parametres.models import Dossier

class UserSerializer(serializers.ModelSerializer):
    dossiers = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Dossier.objects.all(),
        required=False
    )
    class Meta:
        model = User
        fields = ['id', 'email', 'nom', 'role', 'site', 'photo_profil', 'is_active', 'dossiers']
        read_only_fields = ['id']

class UserCreateSerializer(serializers.ModelSerializer):
    dossiers = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Dossier.objects.all(),
        required=False
    )
    class Meta:
        model = User
        fields = ['id', 'email', 'nom', 'role', 'site', 'photo_profil', 'is_active', 'password', 'dossiers']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        dossiers = validated_data.pop('dossiers', [])
        user = User.objects.create_user(password=password, **validated_data)
        user.dossiers.set(dossiers)
        return user

class RolePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolePermission
        fields = ['id', 'role', 'permissions']
