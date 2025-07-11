from django.views.generic import TemplateView
from journeys.models import Journey, Country, City
from itineraries.models import Itinerary, Location, LocationPhoto, ItineraryPhoto



class HomeView(TemplateView):
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Hina 的旅行日記'
        context['total_cities'] = City.objects.count()
        context['total_photos'] = LocationPhoto.objects.count()
        context['total_days'] = Itinerary.objects.count()
        context['highlighted_journeys'] = Journey.objects.filter(
            is_highlighted=True).order_by('-updated_at')[:3]
        context['recent_journeys'] = Journey.objects.order_by('-created_at')[:3]
        return context
