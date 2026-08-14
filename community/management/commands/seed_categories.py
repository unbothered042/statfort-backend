from django.core.management.base import BaseCommand
from community.models import ForumCategory


class Command(BaseCommand):
    help = 'Seed forum categories'

    def handle(self, *args, **kwargs):
        categories = [
            {'name': 'Fortnite', 'slug': 'fortnite', 'description': 'Fortnite builds, stats, clips and discussion.', 'game': 'fortnite', 'is_premium': False, 'order': 1},
            {'name': 'Apex Legends', 'slug': 'apex-legends', 'description': 'Apex Legends legends, loadouts and ranked talk.', 'game': 'apex-legends', 'is_premium': False, 'order': 2},
            {'name': 'COD Mobile', 'slug': 'cod-mobile', 'description': 'COD Mobile tips, loadouts and stat discussions.', 'game': 'cod-mobile', 'is_premium': False, 'order': 3},
            {'name': 'eFootball', 'slug': 'efootball', 'description': 'eFootball builds, formations, and match discussion.', 'game': 'efootball', 'is_premium': False, 'order': 4},
            {'name': 'Stat Reviews', 'slug': 'stat-reviews', 'description': 'Post your stats and get feedback from the community.', 'game': None, 'is_premium': False, 'order': 5},
            {'name': 'Elite Discussion', 'slug': 'elite-discussion', 'description': 'Premium only. High level strategy and competitive discussion.', 'game': None, 'is_premium': True, 'order': 6},
            {'name': 'Strategy Breakdown', 'slug': 'strategy-breakdown', 'description': 'Premium only. Deep dive strategy breakdowns per game.', 'game': None, 'is_premium': True, 'order': 7},
        ]

        for cat in categories:
            obj, created = ForumCategory.objects.get_or_create(
                slug=cat['slug'],
                defaults=cat
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created: {obj.name}"))
            else:
                self.stdout.write(f"Already exists: {obj.name}")

        self.stdout.write(self.style.SUCCESS(f"Done. Total categories: {ForumCategory.objects.count()}"))