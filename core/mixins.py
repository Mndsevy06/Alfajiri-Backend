from rest_framework import viewsets

class DossierScopedViewSetMixin:
    """
    Mixin for ViewSets that filters queries based on X-Entite-ID header 
    and automatically assigns it to new objects. Enforces authorization checks
    to ensure non-SuperAdmin users are assigned to the target dossier.
    """
    def get_queryset(self):
        queryset = super().get_queryset()
        entite_id = self.request.headers.get('X-Entite-ID')
        user = self.request.user
        
        if entite_id:
            # Vérifier l'accès de l'utilisateur à cette entité (dossier)
            if user and user.is_authenticated and user.role != 'Super Admin':
                if not user.dossiers.filter(id=entite_id).exists():
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied("Vous n'êtes pas autorisé à accéder à cette entité.")

            # Check if the model has a 'dossier' field
            if hasattr(queryset.model, 'dossier'):
                queryset = queryset.filter(dossier_id=entite_id)
        else:
            # If no entite_id is provided, return nothing for scoped models
            if hasattr(queryset.model, 'dossier'):
                queryset = queryset.none()
        
        return queryset
        
    def perform_create(self, serializer):
        entite_id = self.request.headers.get('X-Entite-ID')
        user = self.request.user
        
        if entite_id:
            # Vérifier l'autorisation avant de créer des données
            if user and user.is_authenticated and user.role != 'Super Admin':
                if not user.dossiers.filter(id=entite_id).exists():
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied("Vous n'êtes pas autorisé à modifier cette entité.")
            
            if hasattr(serializer.Meta.model, 'dossier'):
                serializer.save(dossier_id=entite_id)
            else:
                serializer.save()
        else:
            serializer.save()
