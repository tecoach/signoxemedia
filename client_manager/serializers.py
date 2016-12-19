# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from rest_framework import serializers

from client_manager.models import Client, Features

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    """ Serializer for client profile. """

    class Meta:
        model = Client
        fields = (
            'organisation_name', 'organisation_address', 'name',
            'primary_contact_name', 'primary_contact_email', 'primary_contact_phone',
            'technical_contact_name', 'technical_contact_email', 'technical_contact_phone',
            'financial_contact_name', 'financial_contact_email', 'financial_contact_phone',
        )
        read_only_fields = ('name',)


class FeaturesSerializer(serializers.ModelSerializer):
    """ Serializer for client features. """

    class Meta:
        model = Features
        fields = ('screenshots', 'smart_notice_board')
        read_only_fields = ('screenshots', 'smart_notice_board')


class UserClientSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(source='profile.client')
    features = FeaturesSerializer(source='profile.client.features')
    renewal_date = serializers.CharField(source='profile.client.subscription.renewal_date')
    next_renewal_date = serializers.CharField(
            source='profile.client.subscription.next_renewal_date')
    activation_date = serializers.DateField(source='profile.client.subscription.renewal_date')

    def update(self, instance, validated_data):
        """ Handle updating user profile """
        profile = validated_data.pop('profile', {}).get('client')
        if profile is not None:
            client = self.instance.profile.client
            ps = ProfileSerializer(data=profile, partial=True, instance=client)
            if ps.is_valid():
                ps.save()
        return super().update(instance, validated_data)

    class Meta:
        model = User
        fields = ('username', 'email', 'profile', 'features',
                  'renewal_date', 'next_renewal_date', 'activation_date',)
        read_only_fields = ('username', 'renewal_date', 'next_renewal_date', 'activation_date',
                            'features')
