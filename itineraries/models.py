from django.db import models
from journeys.models import Journey
import uuid


class TimeSlotChoices(models.TextChoices):
    MORNING = 'morning', '上午'
    AFTERNOON = 'afternoon', '下午'
    EVENING = 'evening', '晚上'


# Create your models here.
class Itinerary(models.Model):
    journey = models.ForeignKey(Journey, on_delete=models.CASCADE)

    title = models.CharField(max_length=200, help_text="行程標題")
    description = models.CharField(max_length=300, help_text="行程描述")
    start_date = models.DateField(help_text="行程開始日期")

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "行程"
        verbose_name_plural = "行程列表"

    def __str__(self):
        return f"{self.journey.title} - {self.title}"


def itinerary_photo_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{instance.uuid}.{ext}"
    return f"itinerary_photos/{filename}"


class ItineraryPhoto(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    itinerary = models.OneToOneField(Itinerary, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=itinerary_photo_upload_path, help_text="行程圖片")
    caption = models.CharField(max_length=255, blank=True, null=True, help_text="圖片說明")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "行程照片"
        verbose_name_plural = "行程照片列表"

    def __str__(self):
        return f"{self.itinerary.title} - 照片"


class Location(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, help_text="地點名稱")
    description = models.CharField(max_length=300, blank=True, null=True, help_text="地點描述")
    google_maps_url = models.CharField(max_length=1000, blank=True, null=True, help_text="Google Maps 地點網址")
    address = models.CharField(max_length=500, blank=True, null=True, help_text="地址")
    latitude = models.FloatField(blank=True, null=True, help_text="緯度")
    longitude = models.FloatField(blank=True, null=True, help_text="經度")
    rating = models.FloatField(blank=True, null=True, help_text="評分")
    place_types = models.CharField(max_length=200, blank=True, null=True, help_text="地點類型")
    arrived_hour = models.IntegerField(blank=True, null=True, help_text="到達小時 (0-23)")
    arrived_minute = models.IntegerField(blank=True, null=True, help_text="到達分鐘 (0-59)")
    departure_hour = models.IntegerField(blank=True, null=True, help_text="離開小時 (0-23)")
    departure_minute = models.IntegerField(blank=True, null=True, help_text="離開分鐘 (0-59)")
    order = models.PositiveIntegerField(default=0, help_text="在行程中的順序")
    time_slot = models.CharField(max_length=50, blank=True, null=False,
                                 default=TimeSlotChoices.MORNING,
                                 choices=TimeSlotChoices.choices,
                                 help_text="時間段 (例如: '上午', '下午', '晚上')")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "地點"
        verbose_name_plural = "地點列表"
        ordering = ['order']

    def __str__(self):
        return f"{self.itinerary.title} - {self.name}"


def location_photo_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{instance.uuid}.{ext}"
    return f"location_photos/{instance.location.itinerary.journey.city}/{filename}"


class LocationPhoto(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=location_photo_upload_path, help_text="地點圖片")
    caption = models.CharField(max_length=255, blank=True, null=True, help_text="圖片說明")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "地點照片"
        verbose_name_plural = "地點照片列表"

    def __str__(self):
        return f"{self.location.name} - 照片"
