from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import BasePermission
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
                'is_active': u.is_active,
                'is_verified': u.is_verified,
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