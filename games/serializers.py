from rest_framework import serializers
from .models import Game, PlayerGame


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ['id', 'name', 'slug', 'is_active']


class PlayerGameSerializer(serializers.ModelSerializer):
    game = GameSerializer(read_only=True)
    game_id = serializers.PrimaryKeyRelatedField(
        queryset=Game.objects.all(), source='game', write_only=True
    )

    class Meta:
        model = PlayerGame
        fields = ['id', 'game', 'game_id', 'gaming_id', 'created_at']
        read_only_fields = ['id', 'created_at']