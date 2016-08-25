from django.contrib.auth.models import User, Group
from rest_framework import serializers

from main.models import Project, Site, Dataset, GenericRecord, Observation, SpeciesObservationSchema


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')


class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    timezone = serializers.CharField()

    class Meta:
        model = Project
        fields = '__all__'
