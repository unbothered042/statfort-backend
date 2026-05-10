from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.core.cache import cache
from stats.models import PlayerStats


class LeaderboardView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, game_slug):
        cache_key = f'leaderboard_{game_slug}'
        cached = cache.get(cache_key)

        if cached is not None:
            return Response(cached, status=status.HTTP_200_OK)

        stats = PlayerStats.objects.filter(
            player_game__game__slug=game_slug,
            status='approved'
        ).order_by('-score', '-kills', '-wins')[:100]

        data = []
        for rank, stat in enumerate(stats, start=1):
            data.append({
                'rank': rank,
                'username': stat.player_game.gaming_id,
                'game': stat.player_game.game.name,
                'kills': stat.kills,
                'deaths': stat.deaths,
                'assists': stat.assists,
                'wins': stat.wins,
                'matches_played': stat.matches_played,
                'kd_ratio': stat.kd_ratio,
                'win_rate': stat.win_rate,
                'score': stat.score,
            })

        cache.set(cache_key, data, 300)
        return Response(data, status=status.HTTP_200_OK)