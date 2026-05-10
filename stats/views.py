from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, BasePermission
from django.core.cache import cache
from .models import PlayerStats
from .serializers import PlayerStatsSerializer, CODStatsSubmitSerializer
from games.models import PlayerGame
import os
import base64
import json
import requests
from groq import Groq


class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


def fetch_fortnite_stats(gaming_id):
    try:
        api_key = os.getenv('FORTNITE_API_KEY')
        url = "https://fortnite-api.com/v2/stats/br/v2"
        headers = {"Authorization": api_key}
        params = {"name": gaming_id}
        response = requests.get(url, headers=headers, params=params)
        return response.json()
    except Exception as e:
        return {'status': 500, 'error': str(e)}


def fetch_apex_stats(gaming_id, platform='PC'):
    try:
        api_key = os.getenv('APEX_API_KEY')
        url = "https://api.mozambiquehe.re/bridge"
        params = {
            "auth": api_key,
            "player": gaming_id,
            "platform": platform,
        }
        response = requests.get(url, params=params)
        return response.json()
    except Exception as e:
        return {'Error': str(e)}


def verify_screenshot_with_ai(screenshot_file, gaming_id, game_name):
    try:
        screenshot_file.seek(0)
        image_data = base64.b64encode(screenshot_file.read()).decode('utf-8')
        ext = screenshot_file.name.split('.')[-1].lower()
        media_type = 'image/png' if ext == 'png' else 'image/jpeg'

        client = Groq(api_key=os.getenv('GROQ_API_KEY'))

        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_data}"
                            }
                        },
                        {
                            "type": "text",
                            "text": f"""You are a gaming stats verification system. Analyze this screenshot and verify if it shows legitimate {game_name} game statistics for the player with gaming ID: {gaming_id}.

Check for:
1. Is this a real {game_name} stats screenshot?
2. Does it show actual game statistics (kills, deaths, wins, matches)?
3. Does the username/gaming ID match or is it visible?
4. Does the screenshot appear authentic and unedited?

Respond with ONLY a JSON object in this exact format:
{{"verified": true/false, "reason": "brief explanation", "kills": number_or_null, "deaths": number_or_null, "wins": number_or_null, "matches_played": number_or_null}}

Return JSON only, no extra text."""
                        }
                    ]
                }
            ],
            max_tokens=500,
        )

        result = response.choices[0].message.content.strip()
        if result.startswith("```"):
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result[4:]

        return json.loads(result.strip())

    except Exception as e:
        return {"verified": False, "reason": str(e)}


class FortniteStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        player_game_id = request.data.get('player_game_id')

        if not player_game_id:
            return Response({'error': 'player_game_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            player_game = PlayerGame.objects.get(id=player_game_id, user=request.user, game__slug='fortnite')
        except PlayerGame.DoesNotExist:
            return Response({'error': 'Fortnite player game not found.'}, status=status.HTTP_404_NOT_FOUND)

        api_response = fetch_fortnite_stats(player_game.gaming_id)

        if api_response.get('status') != 200:
            return Response({'error': api_response.get('error', 'Failed to fetch stats. Make sure your Fortnite profile is set to public.')}, status=status.HTTP_400_BAD_REQUEST)

        data = api_response.get('data', {})
        overall = data.get('stats', {}).get('all', {}).get('overall', {})

        kills = overall.get('kills', 0)
        deaths = overall.get('deaths', 0)
        wins = overall.get('wins', 0)
        matches_played = overall.get('matches', 0)
        score = overall.get('score', 0)

        stats, created = PlayerStats.objects.update_or_create(
            player_game=player_game,
            defaults={
                'kills': kills,
                'deaths': deaths,
                'assists': 0,
                'wins': wins,
                'matches_played': matches_played,
                'score': score,
                'status': 'approved',
            }
        )

        cache.delete(f'leaderboard_{player_game.game.slug}')
        cache.delete(f'player_stats_{request.user.id}')

        serializer = PlayerStatsSerializer(stats)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ApexStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        player_game_id = request.data.get('player_game_id')
        platform = request.data.get('platform', 'PC')

        if not player_game_id:
            return Response({'error': 'player_game_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            player_game = PlayerGame.objects.get(id=player_game_id, user=request.user, game__slug='apex-legends')
        except PlayerGame.DoesNotExist:
            return Response({'error': 'Apex Legends player game not found.'}, status=status.HTTP_404_NOT_FOUND)

        api_response = fetch_apex_stats(player_game.gaming_id, platform)

        if 'Error' in api_response:
            return Response({'error': api_response['Error']}, status=status.HTTP_400_BAD_REQUEST)

        try:
            total_kills = api_response.get('total', {}).get('kills', {}).get('value', 0)
            total_deaths = api_response.get('total', {}).get('deaths', {}).get('value', 0)
            total_games = api_response.get('total', {}).get('games_played', {}).get('value', 0)
            total_wins = api_response.get('total', {}).get('wins', {}).get('value', 0)
            score = api_response.get('total', {}).get('rank_score', {}).get('value', 0)
        except Exception:
            total_kills = 0
            total_deaths = 0
            total_games = 0
            total_wins = 0
            score = 0

        stats, created = PlayerStats.objects.update_or_create(
            player_game=player_game,
            defaults={
                'kills': total_kills,
                'deaths': total_deaths,
                'assists': 0,
                'wins': total_wins,
                'matches_played': total_games,
                'score': score,
                'status': 'approved',
            }
        )

        cache.delete(f'leaderboard_{player_game.game.slug}')
        cache.delete(f'player_stats_{request.user.id}')

        serializer = PlayerStatsSerializer(stats)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CODStatsSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CODStatsSubmitSerializer(data=request.data)
        if serializer.is_valid():
            player_game_id = serializer.validated_data['player_game_id']

            try:
                player_game = PlayerGame.objects.get(id=player_game_id, user=request.user, game__slug='cod-mobile')
            except PlayerGame.DoesNotExist:
                return Response({'error': 'COD Mobile player game not found.'}, status=status.HTTP_404_NOT_FOUND)

            screenshot = serializer.validated_data['screenshot']
            ai_result = verify_screenshot_with_ai(screenshot, player_game.gaming_id, 'COD Mobile')

            if not ai_result.get('verified', False):
                return Response({
                    'error': f'Screenshot verification failed. {ai_result.get("reason", "Please submit a clear screenshot of your COD Mobile stats.")}',
                }, status=status.HTTP_400_BAD_REQUEST)

            ai_kills = ai_result.get('kills') or serializer.validated_data['kills']
            ai_deaths = ai_result.get('deaths') or serializer.validated_data['deaths']
            ai_wins = ai_result.get('wins') or serializer.validated_data['wins']
            ai_matches = ai_result.get('matches_played') or serializer.validated_data['matches_played']

            screenshot.seek(0)
            stats, created = PlayerStats.objects.update_or_create(
                player_game=player_game,
                defaults={
                    'kills': ai_kills,
                    'deaths': ai_deaths,
                    'assists': serializer.validated_data.get('assists', 0),
                    'wins': ai_wins,
                    'matches_played': ai_matches,
                    'score': serializer.validated_data['score'],
                    'screenshot': screenshot,
                    'status': 'approved',
                }
            )

            cache.delete(f'leaderboard_{player_game.game.slug}')
            cache.delete(f'player_stats_{request.user.id}')

            stat_serializer = PlayerStatsSerializer(stats)
            return Response({
                'message': 'Stats verified and approved by AI.',
                'data': stat_serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PlayerStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cache_key = f'player_stats_{request.user.id}'
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached, status=status.HTTP_200_OK)

        stats = PlayerStats.objects.filter(
            player_game__user=request.user,
            status='approved'
        )
        serializer = PlayerStatsSerializer(stats, many=True)
        cache.set(cache_key, serializer.data, 120)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminStatsView(APIView):
    permission_classes = [IsSuperUser]

    def get(self, request):
        stats = PlayerStats.objects.all().order_by('-submitted_at')
        serializer = PlayerStatsSerializer(stats, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)