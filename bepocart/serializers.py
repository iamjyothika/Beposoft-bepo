from rest_framework import serializers
from beposoft_app.models import *




class ProductSerilizers(serializers.ModelSerializer):
    class Meta :
        model = Products
        fields = "__all__"
        