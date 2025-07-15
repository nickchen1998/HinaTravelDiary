from django.apps import AppConfig


class ItinerariesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'itineraries'
    
    def ready(self):
        """
        應用程式啟動時載入信號處理器
        """
        import itineraries.signals
