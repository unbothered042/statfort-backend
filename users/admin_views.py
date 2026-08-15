from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import BasePermission
from django.utils import timezone
from django.db.models import ProtectedError
from django.db import IntegrityError
from django.core.cache import cache
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
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Capture which games this user played before deletion, so we can
        # invalidate their cached leaderboards afterward (leaderboards are
        # cached separately from the DB and won't auto-clear on their own).
        try:
            game_slugs = list(user.player_games.values_list('game__slug', flat=True))
        except Exception:
            game_slugs = []

        try:
            self._force_delete_user(user)
        except Exception as e:
            return Response({
                'error': f'Failed to delete user: {str(e)}',
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        for slug in game_slugs:
            cache.delete(f'leaderboard_{slug}')
        cache.delete(f'player_stats_{id}')

        return Response({
            'message': 'User and all related records (stats, squad setups, insights, community activity, and leaderboard entries) deleted successfully.',
        }, status=status.HTTP_200_OK)

    def _force_delete_user(self, user, max_attempts=10):
        """Deletes the user, cascading through everything Django's CASCADE
        relations already handle automatically (PlayerGame, PlayerStats,
        EfootballSquad, Insight, etc.).

        If any relation elsewhere in the codebase is set to PROTECT (e.g. a
        community post/comment model preserving authorship), Django blocks
        the delete with a ProtectedError instead of silently cascading. This
        loop catches that, deletes the specific objects that were blocking
        it, and retries — repeating until the user (and everything attached
        to them, transitively) is fully gone. This works regardless of which
        app or model is doing the protecting, so it doesn't require knowing
        every model in advance.
        """
        for _ in range(max_attempts):
            try:
                user.delete()
                return
            except ProtectedError as e:
                for obj in e.protected_objects:
                    obj.delete()

        # If we somehow still can't delete after max_attempts, let the final
        # error surface naturally rather than looping forever.
        user.delete()


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