from rest_framework import viewsets

class DossierScopedViewSetMixin:
    """
    Mixin for ViewSets that filters queries based on X-Entite-ID header 
    and automatically assigns it to new objects.
    """
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Don't filter if action is metadata or swagger related, though typically they don't hit here
        entite_id = self.request.headers.get('X-Entite-ID')
        
        if entite_id:
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
        
        if entite_id and hasattr(serializer.Meta.model, 'dossier'):
            # Automatically save the dossier if provided
            # We assume parametres.Dossier is available
            serializer.save(dossier_id=entite_id)
        else:
            serializer.save()
