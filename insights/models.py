from django.db import models
from users.models import User
from games.models import PlayerGame


class Insight(models.Model):
    player_game = models.OneToOneField(PlayerGame, on_delete=models.CASCADE, related_name='insight')
    content = models.TextField()
    generated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.player_game.user.email} - {self.player_game.game.name}"