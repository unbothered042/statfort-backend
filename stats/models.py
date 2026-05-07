from django.db import models
from users.models import User
from games.models import Game, PlayerGame


class PlayerStats(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    player_game = models.ForeignKey(PlayerGame, on_delete=models.CASCADE, related_name='stats')
    kills = models.IntegerField(default=0)
    deaths = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    matches_played = models.IntegerField(default=0)
    kd_ratio = models.FloatField(default=0.0)
    win_rate = models.FloatField(default=0.0)
    score = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='approved')
    screenshot = models.ImageField(upload_to='screenshots/', null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-score']

    def __str__(self):
        return f"{self.player_game.user.email} - {self.player_game.game.name}"

    def calculate_kd(self):
        if self.deaths == 0:
            return self.kills
        return round(self.kills / self.deaths, 2)

    def calculate_win_rate(self):
        if self.matches_played == 0:
            return 0.0
        return round((self.wins / self.matches_played) * 100, 2)

    def save(self, *args, **kwargs):
        self.kd_ratio = self.calculate_kd()
        self.win_rate = self.calculate_win_rate()
        super().save(*args, **kwargs)