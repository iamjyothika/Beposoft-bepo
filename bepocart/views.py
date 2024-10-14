from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from beposoft_app.models import Products
from .serializers import ProductSerilizers



class ProductListView(APIView):
    def get(self,request):
        products = Products.objects.all()
        serializer = ProductSerilizers(products, many=True)
        return Response(serializer.data)