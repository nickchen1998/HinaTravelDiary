from django.urls import path
from . import views

app_name = 'itineraries'

urlpatterns = [
    path('journeys/<int:journey_id>/itineraries/', views.itinerary_list, name='itinerary_list'),
    path('itineraries/<int:itinerary_id>/locations/', views.location_list, name='location_list'),
    path('itineraries/<int:itinerary_id>/map-data/', views.location_map_data, name='location_map_data'),
]