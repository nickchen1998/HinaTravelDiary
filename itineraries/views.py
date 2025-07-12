from django.shortcuts import render, get_object_or_404
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
