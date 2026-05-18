from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Insight
from .serializers import InsightSerializer
from .ai_service import generate_insight, generate_elite_insights
from stats.models import PlayerStats
from games.models import PlayerGame


class InsightView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, player_game_id):
        user = request.user

        if not user.can_use_ai_insight():
            limit = user.get_ai_limit()
            reset_at = user.ai_limit_reset_at
            return Response({
                'error': f'Daily AI limit reached. You have used {limit}/{limit} insights today.',
                'limit_exhausted': True,
                'reset_at': reset_at,
                'is_premium': user.check_premium(),
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        try:
            player_game = PlayerGame.objects.get(id=player_game_id, user=request.user)
        except PlayerGame.DoesNotExist:
            return Response({'error': 'Player game not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            stats = PlayerStats.objects.get(player_game=player_game, status='approved')
        except PlayerStats.DoesNotExist:
            return Response({'error': 'No approved stats found.'}, status=status.HTTP_404_NOT_FOUND)

        content = generate_insight(
            game_name=player_game.game.name,
            kills=stats.kills,
            deaths=stats.deaths,
            assists=stats.assists,
            wins=stats.wins,
            matches_played=stats.matches_played,
            kd_ratio=stats.kd_ratio,
            win_rate=stats.win_rate,
        )

        user.ai_insight_count += 1
        user.save()

        insight, created = Insight.objects.update_or_create(
            player_game=player_game,
            defaults={'content': content}
        )

        serializer = InsightSerializer(insight)
        return Response({
            **serializer.data,
            'ai_insight_count': user.ai_insight_count,
            'ai_limit': user.get_ai_limit(),
        }, status=status.HTTP_200_OK)


class EliteInsightView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, player_game_id):
        user = request.user

        if not user.can_use_elite_insight():
            limit = user.get_ai_limit()
            reset_at = user.ai_limit_reset_at
            return Response({
                'error': f'Daily Elite limit reached. You have used {limit}/{limit} analyses today.',
                'limit_exhausted': True,
                'reset_at': reset_at,
                'is_premium': user.check_premium(),
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        try:
            player_game = PlayerGame.objects.get(id=player_game_id, user=request.user)
        except PlayerGame.DoesNotExist:
            return Response({'error': 'Player game not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            stats = PlayerStats.objects.get(player_game=player_game, status='approved')
        except PlayerStats.DoesNotExist:
            return Response({'error': 'No approved stats found.'}, status=status.HTTP_404_NOT_FOUND)

        elite = generate_elite_insights(
            game_name=player_game.game.name,
            kills=stats.kills,
            deaths=stats.deaths,
            assists=stats.assists,
            wins=stats.wins,
            matches_played=stats.matches_played,
            kd_ratio=stats.kd_ratio,
            win_rate=stats.win_rate,
        )

        user.elite_insight_count += 1
        user.save()

        return Response({
            'elite_insights': elite,
            'elite_insight_count': user.elite_insight_count,
            'ai_limit': user.get_ai_limit(),
        }, status=status.HTTP_200_OK)