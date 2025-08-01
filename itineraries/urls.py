from django.urls import path
from . import views

app_name = 'itineraries'

urlpatterns = [
    path('journeys/<int:journey_id>/itineraries/', views.itinerary_list, name='itinerary_list'),
    path('itineraries/<int:itinerary_id>/locations/', views.location_list, name='location_list'),
    path('itineraries/<int:itinerary_id>/map-data/', views.location_map_data, name='location_map_data'),
    
    # 地點相關路由
    path('itineraries/<int:itinerary_id>/locations/create/', views.create_location, name='create_location'),
    path('itineraries/<int:itinerary_id>/locations/<int:location_id>/edit/', views.edit_location, name='edit_location'),
    path('itineraries/<int:itinerary_id>/locations/<int:location_id>/delete/', views.delete_location, name='delete_location'),
    path('itineraries/<int:itinerary_id>/locations/reorder/', views.reorder_locations, name='reorder_locations'),
]