# scheduler/urls.py
from django.urls import path
from . import views
from .views import json_to_excel

urlpatterns = [
    path('', views.index, name='index'),
    path('json-to-excel/', json_to_excel, name='json_to_excel'),

]