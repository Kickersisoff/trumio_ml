# myapi/urls.py
from django.urls import path
from .views import calculate_skills

urlpatterns = [
    path('calculate-skills/', calculate_skills, name='calculate_skills'),
]
