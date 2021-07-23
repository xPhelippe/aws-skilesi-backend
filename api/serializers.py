from rest_framework import serializers

from .models import *
from django.contrib.auth.models import User


class ProfileSerializer(serializers.Serializer):

    class Meta:
        model = Profile
        fields = ["investmentType"]


class StockSerializer(serializers.ModelSerializer):

    class Meta:
        model = Stock
        fields = ["ticker"]


class WatchListSerializer(serializers.ModelSerializer):
    stock = StockSerializer(many=False)

    class Meta:
        model = FavStock
        fields = ['stock']


class UserSerializer(serializers.ModelSerializer):

    watchlist = WatchListSerializer(many=True)

    #profile = ProfileSerializer(many=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'watchlist']

