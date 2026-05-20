from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from .models import ForumCategory, ForumPost, ForumReply, ForumLike, UserRep
from .serializers import ForumCategorySerializer, ForumPostSerializer, ForumReplySerializer


class CategoryListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        categories = ForumCategory.objects.all()
        serializer = ForumCategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PostListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, category_slug):
        category = get_object_or_404(ForumCategory, slug=category_slug)
        posts = ForumPost.objects.filter(category=category).select_related('author', 'author__rep')
        serializer = ForumPostSerializer(posts, many=True, context={'request': request})
        return Response({
            'category': ForumCategorySerializer(category).data,
            'posts': serializer.data,
        }, status=status.HTTP_200_OK)

    def post(self, request, category_slug):
        if not request.user.is_authenticated:
            return Response({'error': 'Login required.'}, status=status.HTTP_401_UNAUTHORIZED)

        category = get_object_or_404(ForumCategory, slug=category_slug)

        if category.is_premium and not request.user.check_premium():
            return Response({'error': 'Premium required to post in this room.', 'requires_premium': True}, status=status.HTTP_403_FORBIDDEN)

        title = request.data.get('title', '').strip()
        content = request.data.get('content', '').strip()

        if not title:
            return Response({'error': 'Title is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if not content:
            return Response({'error': 'Content is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if len(title) > 200:
            return Response({'error': 'Title too long. Max 200 characters.'}, status=status.HTTP_400_BAD_REQUEST)

        post = ForumPost.objects.create(
            category=category,
            author=request.user,
            title=title,
            content=content,
        )

        UserRep.add_points(request.user, 5)

        serializer = ForumPostSerializer(post, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PostDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, post_id):
        post = get_object_or_404(ForumPost, id=post_id)
        post.views += 1
        post.save()
        replies = ForumReply.objects.filter(post=post).select_related('author', 'author__rep')
        post_serializer = ForumPostSerializer(post, context={'request': request})
        reply_serializer = ForumReplySerializer(replies, many=True, context={'request': request})
        return Response({
            'post': post_serializer.data,
            'replies': reply_serializer.data,
        }, status=status.HTTP_200_OK)

    def put(self, request, post_id):
        if not request.user.is_authenticated:
            return Response({'error': 'Login required.'}, status=status.HTTP_401_UNAUTHORIZED)

        post = get_object_or_404(ForumPost, id=post_id)

        if post.author != request.user and not request.user.is_superuser:
            return Response({'error': 'You can only edit your own posts.'}, status=status.HTTP_403_FORBIDDEN)

        title = request.data.get('title', '').strip()
        content = request.data.get('content', '').strip()

        if not title or not content:
            return Response({'error': 'Title and content are required.'}, status=status.HTTP_400_BAD_REQUEST)

        post.title = title
        post.content = content
        post.is_edited = True
        post.save()

        serializer = ForumPostSerializer(post, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, post_id):
        if not request.user.is_authenticated:
            return Response({'error': 'Login required.'}, status=status.HTTP_401_UNAUTHORIZED)

        post = get_object_or_404(ForumPost, id=post_id)

        if post.author != request.user and not request.user.is_superuser:
            return Response({'error': 'You can only delete your own posts.'}, status=status.HTTP_403_FORBIDDEN)

        UserRep.remove_points(request.user, 5)
        post.delete()
        return Response({'message': 'Post deleted.'}, status=status.HTTP_200_OK)


class ReplyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(ForumPost, id=post_id)

        if post.category.is_premium and not request.user.check_premium():
            return Response({'error': 'Premium required to reply in this room.', 'requires_premium': True}, status=status.HTTP_403_FORBIDDEN)

        content = request.data.get('content', '').strip()
        if not content:
            return Response({'error': 'Content is required.'}, status=status.HTTP_400_BAD_REQUEST)

        reply = ForumReply.objects.create(
            post=post,
            author=request.user,
            content=content,
        )

        UserRep.add_points(post.author, 2)

        serializer = ForumReplySerializer(reply, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ReplyDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, reply_id):
        reply = get_object_or_404(ForumReply, id=reply_id)

        if reply.author != request.user and not request.user.is_superuser:
            return Response({'error': 'You can only edit your own replies.'}, status=status.HTTP_403_FORBIDDEN)

        content = request.data.get('content', '').strip()
        if not content:
            return Response({'error': 'Content is required.'}, status=status.HTTP_400_BAD_REQUEST)

        reply.content = content
        reply.is_edited = True
        reply.save()

        serializer = ForumReplySerializer(reply, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, reply_id):
        reply = get_object_or_404(ForumReply, id=reply_id)

        if reply.author != request.user and not request.user.is_superuser:
            return Response({'error': 'You can only delete your own replies.'}, status=status.HTTP_403_FORBIDDEN)

        reply.delete()
        return Response({'message': 'Reply deleted.'}, status=status.HTTP_200_OK)


class LikePostView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(ForumPost, id=post_id)
        like, created = ForumLike.objects.get_or_create(user=request.user, post=post)

        if not created:
            like.delete()
            UserRep.remove_points(post.author, 1)
            return Response({'liked': False, 'like_count': post.like_count}, status=status.HTTP_200_OK)

        UserRep.add_points(post.author, 1)
        return Response({'liked': True, 'like_count': post.like_count}, status=status.HTTP_200_OK)


class LikeReplyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, reply_id):
        reply = get_object_or_404(ForumReply, id=reply_id)
        like, created = ForumLike.objects.get_or_create(user=request.user, reply=reply)

        if not created:
            like.delete()
            UserRep.remove_points(reply.author, 1)
            return Response({'liked': False, 'like_count': reply.like_count}, status=status.HTTP_200_OK)

        UserRep.add_points(reply.author, 1)
        return Response({'liked': True, 'like_count': reply.like_count}, status=status.HTTP_200_OK)