# myapi/serializers.py
# from rest_framework import serializers

# class ResultSerializer(serializers.Serializer):
#     result = serializers.IntegerField()

from rest_framework import serializers

class SkillsSerializer(serializers.Serializer):
    skills = serializers.ListField(child=serializers.CharField())
