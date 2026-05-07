from django.urls import path
from . import views

urlpatterns = [
    path('<str:game_slug>/', views.LeaderboardView.as_view(), name='leaderboard'),
]