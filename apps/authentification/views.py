from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import User, RolePermission
from .serializers import UserSerializer, UserCreateSerializer, RolePermissionSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    @action(detail=False, methods=['get', 'patch'])
    def me(self, request):
        user = request.user
        if request.method == 'PATCH':
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        serializer = self.get_serializer(user)
        data = serializer.data
        
        # Add permissions to response
        role_perm = RolePermission.objects.filter(role=user.role).first()
        data['permissions'] = role_perm.permissions if role_perm else {}
        
        return Response(data)

    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        # SEC-4: Seuls les Super Admin peuvent réinitialiser le mot de passe d'un autre utilisateur.
        # Un utilisateur peut changer son propre mot de passe.
        target_user = self.get_object()
        if request.user.pk != target_user.pk and request.user.role not in ['Super Admin', 'Chef Comptable']:
            return Response({'error': 'Permission refusée. Seul un Super Admin peut réinitialiser le mot de passe d\'un autre utilisateur.'}, status=status.HTTP_403_FORBIDDEN)
        new_password = request.data.get('password')
        if not new_password:
            return Response({'error': 'Le mot de passe est requis'}, status=status.HTTP_400_BAD_REQUEST)
        if len(new_password) < 8:
            return Response({'error': 'Le mot de passe doit contenir au moins 8 caractères.'}, status=status.HTTP_400_BAD_REQUEST)
        target_user.set_password(new_password)
        target_user.save()
        return Response({'status': 'Mot de passe réinitialisé avec succès'})

class RolePermissionViewSet(viewsets.ModelViewSet):
    queryset = RolePermission.objects.all().order_by('id')
    serializer_class = RolePermissionSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        data = request.data # Expecting a dict like { "Role Name": { "permission_id": true, ... }, ... }
        for role_name, permissions in data.items():
            RolePermission.objects.update_or_create(
                role=role_name,
                defaults={'permissions': permissions}
            )
        return Response({'status': 'Permissions updated successfully'})
