from django.urls import path
from .views import *




urlpatterns = [
    path('products/',ProductListView.as_view()),
    path('emi/', EmiView.as_view(), name='emi'),
]

