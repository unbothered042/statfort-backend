from django.urls import path
from . import views

urlpatterns = [
    path('categories/', views.CategoryListView.as_view(), name='categories'),
    path('categories/<slug:category_slug>/', views.PostListView.as_view(), name='posts'),
    path('posts/<int:post_id>/', views.PostDetailView.as_view(), name='post-detail'),
    path('posts/<int:post_id>/replies/', views.ReplyView.as_view(), name='replies'),
    path('replies/<int:reply_id>/', views.ReplyDetailView.as_view(), name='reply-detail'),
    path('posts/<int:post_id>/like/', views.LikePostView.as_view(), name='like-post'),
    path('replies/<int:reply_id>/like/', views.LikeReplyView.as_view(), name='like-reply'),
]