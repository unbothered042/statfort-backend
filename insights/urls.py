from django.urls import path
from . import views

urlpatterns = [
    path('<int:player_game_id>/', views.InsightView.as_view(), name='insight'),
    path('<int:player_game_id>/elite/', views.EliteInsightView.as_view(), name='elite-insight'),
]