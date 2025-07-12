from django.shortcuts import render, get_object_or_404
from .models import Country, Journey
from itineraries.models import Itinerary


def journey_list(request, country_id):
    """顯示特定國家的旅程列表"""
    country = get_object_or_404(Country, id=country_id)
    journeys = Journey.objects.filter(country=country).order_by('-start_date')
    
    # 為每個旅程計算行程數量
    for journey in journeys:
        journey.itinerary_count = Itinerary.objects.filter(journey=journey).count()
    
    context = {
        'country': country,
        'journeys': journeys,
    }
    return render(request, 'journeys.html', context)
