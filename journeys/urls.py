from django.urls import path
from . import views

app_name = 'journeys'

urlpatterns = [
    path('countries/<int:country_id>/journeys/', views.journey_list, name='journey_list'),
]