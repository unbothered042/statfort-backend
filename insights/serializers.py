from rest_framework import serializers
from .models import Insight


class InsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Insight
        fields = ['id', 'content', 'generated_at']
        read_only_fields = ['id', 'content', 'generated_at']