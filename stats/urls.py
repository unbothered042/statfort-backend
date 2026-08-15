from django.urls import path
from . import views

urlpatterns = [
    path('fortnite/fetch/', views.FortniteStatsView.as_view(), name='fortnite-stats'),
    path('apex/fetch/', views.ApexStatsView.as_view(), name='apex-stats'),
    path('cod/submit/', views.CODStatsSubmitView.as_view(), name='cod-stats-submit'),
    path('efootball/submit/', views.EFootballStatsSubmitView.as_view(), name='efootball-stats-submit'),
    path('efootball/squad/', views.EfootballSquadView.as_view(), name='efootball-squad'),
    path('efootball/upload-status/', views.EfootballUploadStatusView.as_view(), name='efootball-upload-status'),
    path('my-stats/', views.PlayerStatsView.as_view(), name='my-stats'),
    path('admin/all/', views.AdminStatsView.as_view(), name='admin-stats'),
]