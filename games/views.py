from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Game, PlayerGame
from .serializers import GameSerializer, PlayerGameSerializer


class GameListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        games = Game.objects.filter(is_active=True)
        serializer = GameSerializer(games, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PlayerGameView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        player_games = PlayerGame.objects.filter(user=request.user)
        serializer = PlayerGameSerializer(player_games, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        game_id = request.data.get('game_id')
        gaming_id = request.data.get('gaming_id')

        if not game_id or not gaming_id:
            return Response({'error': 'game_id and gaming_id are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            game = Game.objects.get(id=game_id, is_active=True)
        except Game.DoesNotExist:
            return Response({'error': 'Game not found.'}, status=status.HTTP_404_NOT_FOUND)

        if PlayerGame.objects.filter(user=request.user, game=game).exists():
            return Response({'error': 'You have already registered this game.'}, status=status.HTTP_400_BAD_REQUEST)

        player_game = PlayerGame.objects.create(
            user=request.user,
            game=game,
            gaming_id=gaming_id,
        )
        serializer = PlayerGameSerializer(player_game)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        try:
            player_game = PlayerGame.objects.get(id=pk, user=request.user)
            player_game.delete()
            return Response({'message': 'Game removed successfully.'}, status=status.HTTP_200_OK)
        except PlayerGame.DoesNotExist:
            return Response({'error': 'Player game not found.'}, status=status.HTTP_404_NOT_FOUND)