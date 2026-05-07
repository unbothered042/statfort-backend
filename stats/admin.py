from django.contrib import admin
from .models import PlayerStats


@admin.register(PlayerStats)
class PlayerStatsAdmin(admin.ModelAdmin):
    list_display = ['player_game', 'kills', 'deaths', 'assists', 'wins', 'matches_played', 'kd_ratio', 'win_rate', 'score', 'status']
    list_filter = ['status', 'player_game__game']
    list_editable = ['status']
    search_fields = ['player_game__user__email', 'player_game__gaming_id']