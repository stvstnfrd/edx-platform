from django.contrib.auth.models import User
from rest_framework import serializers
from student.models import UserProfile
from user_api.models import UserPreference
from django_comment_common.models import Role

class RoleSerializer(serializers.ModelSerializer):
    users = serializers.SerializerMethodField('get_users')

    def get_users(self, role):
        users = role.users.all()
        return [user.email for user in users]

    class Meta:
        model = Role
        fields = ('name', 'course_id', 'users')

class UserSerializer(serializers.HyperlinkedModelSerializer):
    name = serializers.SerializerMethodField("get_name")
    preferences = serializers.SerializerMethodField("get_preferences")

    def get_name(self, user):
        profile = UserProfile.objects.get(user=user)
        return profile.name

    def get_preferences(self, user):
        return dict([(pref.key, pref.value) for pref in user.preferences.all()])

    class Meta:
        model = User
        # This list is the minimal set required by the notification service
        fields = ("id", "email", "name", "username", "preferences")
        read_only_fields = ("id", "email", "username")


class UserPreferenceSerializer(serializers.HyperlinkedModelSerializer):
    user = UserSerializer()

    class Meta:
        model = UserPreference
        depth = 1
