from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Insight
from .serializers import InsightSerializer
from .ai_service import generate_insight
from stats.models import PlayerStats
from games.models import PlayerGame


class InsightView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, player_game_id):
        try:
            player_game = PlayerGame.objects.get(id=player_game_id, user=request.user)
        except PlayerGame.DoesNotExist:
            return Response({'error': 'Player game not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            insight = Insight.objects.get(player_game=player_game)
            serializer = InsightSerializer(insight)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Insight.DoesNotExist:
            return Response({'error': 'No insight found. Please generate one first.'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, player_game_id):
        try:
            player_game = PlayerGame.objects.get(id=player_game_id, user=request.user)
        except PlayerGame.DoesNotExist:
            return Response({'error': 'Player game not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            stats = PlayerStats.objects.get(player_game=player_game, status='approved')
        except PlayerStats.DoesNotExist:
            return Response({'error': 'No approved stats found. Please submit or fetch your stats first.'}, status=status.HTTP_404_NOT_FOUND)

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

        insight, created = Insight.objects.update_or_create(
            player_game=player_game,
            defaults={'content': content}
        )

        serializer = InsightSerializer(insight)
        return Response(serializer.data, status=status.HTTP_200_OK)