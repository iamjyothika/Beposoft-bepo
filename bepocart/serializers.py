from rest_framework import serializers
from beposoft_app.models import *
from .models import*




class ProductSerilizers(serializers.ModelSerializer):
    class Meta :
        model = Products
        fields = "__all__"
        



class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = "__all_"
