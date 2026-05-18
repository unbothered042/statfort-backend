from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import BasePermission
from django.utils import timezone
from datetime import timedelta
from .models import User


class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


class AdminUserListView(APIView):
    permission_classes = [IsSuperUser]

    def get(self, request):
        users = User.objects.filter(is_superuser=False).order_by('-created_at')
        data = [
            {
                'id': u.id,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'email': u.email,
                'username': u.username,
                'state': u.state,
                'is_active': u.is_active,
                'is_verified': u.is_verified,
                'is_premium': u.check_premium(),
                'premium_expires_at': u.premium_expires_at,
                'ai_insight_count': u.ai_insight_count,
                'elite_insight_count': u.elite_insight_count,
                'ai_limit': u.get_ai_limit(),
                'created_at': u.created_at,
            }
            for u in users
        ]
        return Response(data, status=status.HTTP_200_OK)


class AdminUserDeleteView(APIView):
    permission_classes = [IsSuperUser]

    def delete(self, request, id):
        try:
            user = User.objects.get(id=id, is_superuser=False)
            user.delete()
            return Response({'message': 'User deleted successfully.'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)


class AdminTogglePremiumView(APIView):
    permission_classes = [IsSuperUser]

    def post(self, request, id):
        try:
            user = User.objects.get(id=id, is_superuser=False)
            action = request.data.get('action')

            if action == 'grant':
                user.is_premium = True
                user.premium_expires_at = timezone.now() + timedelta(days=30)
                user.save()
                return Response({'message': f'Premium granted to {user.email} for 30 days.'}, status=status.HTTP_200_OK)
            elif action == 'revoke':
                user.is_premium = False
                user.premium_expires_at = None
                user.save()
                return Response({'message': f'Premium revoked from {user.email}.'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid action. Use grant or revoke.'}, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)