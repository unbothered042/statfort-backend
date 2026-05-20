from rest_framework import serializers
from .models import ForumCategory, ForumPost, ForumReply, ForumLike, UserRep
from users.models import User


class AuthorSerializer(serializers.ModelSerializer):
    rep_points = serializers.SerializerMethodField()
    is_premium = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'state', 'rep_points', 'is_premium']

    def get_rep_points(self, obj):
        try:
            return obj.rep.points
        except Exception:
            return 0

    def get_is_premium(self, obj):
        return obj.check_premium()


class ForumReplySerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    like_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = ForumReply
        fields = ['id', 'content', 'author', 'like_count', 'is_liked', 'is_edited', 'created_at', 'updated_at']

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False


class ForumPostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    like_count = serializers.IntegerField(read_only=True)
    reply_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)

    class Meta:
        model = ForumPost
        fields = [
            'id', 'title', 'content', 'author', 'category_name', 'category_slug',
            'like_count', 'reply_count', 'is_liked', 'is_pinned', 'views',
            'is_edited', 'created_at', 'updated_at'
        ]

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False


class ForumCategorySerializer(serializers.ModelSerializer):
    post_count = serializers.IntegerField(read_only=True)
    latest_post = serializers.SerializerMethodField()

    class Meta:
        model = ForumCategory
        fields = ['id', 'name', 'slug', 'description', 'game', 'is_premium', 'post_count', 'latest_post', 'order']

    def get_latest_post(self, obj):
        post = obj.latest_post
        if post:
            return {
                'id': post.id,
                'title': post.title,
                'author': post.author.username,
                'created_at': post.created_at,
            }
        return None