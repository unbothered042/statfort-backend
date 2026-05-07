from rest_framework import serializers
from .models import PlayerStats
from games.serializers import PlayerGameSerializer


class PlayerStatsSerializer(serializers.ModelSerializer):
    player_game = PlayerGameSerializer(read_only=True)
    player_game_id = serializers.PrimaryKeyRelatedField(
        queryset=PlayerStats.objects.none(), source='player_game', write_only=True
    )

    class Meta:
        model = PlayerStats
        fields = [
            'id', 'player_game', 'player_game_id', 'kills', 'deaths',
            'assists', 'wins', 'matches_played', 'kd_ratio', 'win_rate',
            'score', 'status', 'screenshot', 'submitted_at',
        ]
        read_only_fields = ['id', 'kd_ratio', 'win_rate', 'status', 'submitted_at']


class CODStatsSubmitSerializer(serializers.Serializer):
    player_game_id = serializers.IntegerField()
    kills = serializers.IntegerField(min_value=0)
    deaths = serializers.IntegerField(min_value=0)
    assists = serializers.IntegerField(min_value=0)
    wins = serializers.IntegerField(min_value=0)
    matches_played = serializers.IntegerField(min_value=1)
    score = serializers.IntegerField(min_value=0)
    screenshot = serializers.ImageField()