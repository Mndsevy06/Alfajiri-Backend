from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(APIView):
    """GET /api/notifications/ — liste des 50 dernières notifications de l'utilisateur"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Notification.objects.filter(user=request.user).order_by('-cree_le')[:50]
        data = NotificationSerializer(qs, many=True).data
        unread_count = Notification.objects.filter(user=request.user, lu=False).count()
        return Response({
            'results': data,
            'unread_count': unread_count,
        })


class NotificationMarkReadView(APIView):
    """PATCH /api/notifications/{id}/read/ — marquer une notification comme lue"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            notif = Notification.objects.get(id=pk, user=request.user)
            notif.lu = True
            notif.save(update_fields=['lu'])
            return Response({'status': 'ok'})
        except Notification.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)


class NotificationMarkAllReadView(APIView):
    """POST /api/notifications/read-all/ — marquer toutes comme lues"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        count = Notification.objects.filter(user=request.user, lu=False).update(lu=True)
        return Response({'marked': count})


class NotificationDeleteView(APIView):
    """DELETE /api/notifications/{id}/ — supprimer une notification"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        Notification.objects.filter(id=pk, user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
