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

    @action(detail=False, methods=['get'])
    def me(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        data = serializer.data
        
        # Add permissions to response
        role_perm = RolePermission.objects.filter(role=user.role).first()
        data['permissions'] = role_perm.permissions if role_perm else {}
        
        return Response(data)

    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        user = self.get_object()
        new_password = request.data.get('password')
        if not new_password:
            return Response({'error': 'Le mot de passe est requis'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
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
