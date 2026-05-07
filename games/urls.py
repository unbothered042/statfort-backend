from django.urls import path
from . import views

urlpatterns = [
    path('', views.GameListView.as_view(), name='game-list'),
    path('my-games/', views.PlayerGameView.as_view(), name='player-games'),
    path('my-games/<int:pk>/', views.PlayerGameView.as_view(), name='player-game-delete'),
]