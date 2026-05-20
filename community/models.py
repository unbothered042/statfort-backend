from django.db import models
from django.utils import timezone
from users.models import User


class ForumCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    game = models.CharField(max_length=50, blank=True, null=True)
    is_premium = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name

    @property
    def post_count(self):
        return self.posts.count()

    @property
    def latest_post(self):
        return self.posts.order_by('-created_at').first()


class ForumPost(models.Model):
    category = models.ForeignKey(ForumCategory, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_pinned = models.BooleanField(default=False)
    views = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return self.title

    @property
    def reply_count(self):
        return self.replies.count()

    @property
    def like_count(self):
        return self.likes.count()


class ForumReply(models.Model):
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='replies')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Reply by {self.author.username} on {self.post.title}"

    @property
    def like_count(self):
        return self.likes.count()


class ForumLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='likes', null=True, blank=True)
    reply = models.ForeignKey(ForumReply, on_delete=models.CASCADE, related_name='likes', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['user', 'post'], ['user', 'reply']]

    def __str__(self):
        return f"{self.user.username} liked something"


class UserRep(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='rep')
    points = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.points} rep"

    @classmethod
    def add_points(cls, user, points):
        rep, created = cls.objects.get_or_create(user=user)
        rep.points += points
        rep.save()
        return rep

    @classmethod
    def remove_points(cls, user, points):
        rep, created = cls.objects.get_or_create(user=user)
        rep.points = max(0, rep.points - points)
        rep.save()
        return rep