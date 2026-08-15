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
    draws = models.IntegerField(default=0)
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


# --- eFootball Elite: Squad Composition (for pairing analysis) ---

PLAYER_TYPE_CHOICES = [
    ('destroyer', 'Destroyer'),
    ('anchor_man', 'Anchor Man'),
    ('extra_frame', 'Extra Frame'),
    ('catalyst', 'Catalyst'),
    ('long_ball_expert', 'Long Ball Expert'),
    ('aerial_threat', 'Aerial Threat'),
    ('box_to_box', 'Box-to-Box'),
    ('deep_lying_playmaker', 'Deep-Lying Playmaker'),
    ('the_incisive_run', 'The Incisive Run'),
    ('prolific_winger', 'Prolific Winger'),
    ('cross_specialist', 'Cross Specialist'),
    ('speedster', 'Speedster'),
    ('goal_poacher', 'Goal Poacher'),
    ('target_man', 'Target Man'),
    ('dummy_runner', 'Dummy Runner'),
]


class EfootballSquad(models.Model):
    """Stores a user's key pack player types for the 7 synergy-critical
    positions used in Elite Tier squad pairing analysis."""

    player_game = models.OneToOneField(PlayerGame, on_delete=models.CASCADE, related_name='efootball_squad')

    gk_type = models.CharField(max_length=30, choices=PLAYER_TYPE_CHOICES)
    cb1_type = models.CharField(max_length=30, choices=PLAYER_TYPE_CHOICES)
    cb2_type = models.CharField(max_length=30, choices=PLAYER_TYPE_CHOICES)
    cdm_type = models.CharField(max_length=30, choices=PLAYER_TYPE_CHOICES)
    lw_type = models.CharField(max_length=30, choices=PLAYER_TYPE_CHOICES)
    rw_type = models.CharField(max_length=30, choices=PLAYER_TYPE_CHOICES)
    st_type = models.CharField(max_length=30, choices=PLAYER_TYPE_CHOICES)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.player_game.user.email} - Squad Setup"


# --- eFootball Screenshot Verification Rate Limiting (3/day, since each check calls the AI) ---

class EfootballScreenshotUpload(models.Model):
    """One row per eFootball screenshot verification attempt. Used to cap
    verification calls to 3 per user per calendar day."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='efootball_screenshot_uploads')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.uploaded_at.date()}"