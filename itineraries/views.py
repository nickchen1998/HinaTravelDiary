from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from journeys.models import Journey
from .models import Itinerary, Location


def itinerary_list(request, journey_id):
    journey = get_object_or_404(Journey, id=journey_id)
    itineraries = Itinerary.objects.filter(journey=journey).order_by('start_date')
    
    context = {
        'journey': journey,
        'itineraries': itineraries,
    }
    return render(request, 'itineraries.html', context)


def location_list(request, itinerary_id):
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    locations = Location.objects.filter(itinerary=itinerary).order_by('order')
    
    context = {
        'itinerary': itinerary,
        'locations': locations,
    }
    return render(request, 'locations.html', context)


@require_GET
def location_map_data(request, itinerary_id):
    """提供地圖資料的 API endpoint"""
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    locations = Location.objects.filter(itinerary=itinerary).order_by('order')
    
    # 只返回有座標的地點
    location_data = []
    for location in locations:
        if location.latitude and location.longitude:
            location_data.append({
                'name': location.name,
                'description': location.description or '',
                'address': location.address or '',
                'rating': location.rating,
                'order': location.order,
                'lat': float(location.latitude),
                'lng': float(location.longitude),
                'url': location.google_maps_url or ''
            })
    
    return JsonResponse({
        'locations': location_data,
        'api_key': getattr(settings, 'GOOGLE_MAPS_API_KEY', ''),
        'itinerary_title': itinerary.title
    })
