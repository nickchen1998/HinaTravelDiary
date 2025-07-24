from django.urls import path
from . import views

app_name = 'journeys'

urlpatterns = [
    path('countries/<int:country_id>/journeys/', views.journey_list, name='journey_list'),
    path('countries/<int:country_id>/journeys/create/', views.create_journey, name='create_journey'),
    path('countries/<int:country_id>/journeys/<int:journey_id>/edit/', views.edit_journey, name='edit_journey'),
]