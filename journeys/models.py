from django.db import models
import uuid
from django.contrib.auth.models import User


class Country(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="國家名稱")
    english_name = models.CharField(max_length=100, unique=True, help_text="國家英文名稱")
    country_code = models.CharField(max_length=100, unique=True, help_text="國家代碼")
    is_highlighted = models.BooleanField(default=False, help_text="是否為精選國家")

    class Meta:
        verbose_name = "國家"
        verbose_name_plural = "國家列表"
    
    def __str__(self):
        return self.name


class City(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='cities')
    name = models.CharField(max_length=100, help_text="城市名稱")
    english_name = models.CharField(max_length=100, help_text="城市英文名稱")

    class Meta:
        verbose_name = "城市"
        verbose_name_plural = "城市列表"
        unique_together = ('country', 'name')
    
    def __str__(self):
        return f"{self.country.name} - {self.name}"


# Create your models here.
class Journey(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    city = models.ForeignKey(City, on_delete=models.CASCADE, blank=True, null=True)

    title = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()

    is_highlighted = models.BooleanField(default=False, help_text="是否為精選旅程")
    author = models.ForeignKey(User, on_delete=models.CASCADE, help_text="旅程作者", default=1)

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "旅程"
        verbose_name_plural = "旅程列表"
    
    def __str__(self):
        return f"{self.country.name} - {self.title}"


def journey_photo_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{instance.uuid}.{ext}"
    return f"journey_photos/{filename}"


class JourneyPhoto(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    journey = models.OneToOneField(Journey, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=journey_photo_upload_path)
    caption = models.CharField(max_length=255, blank=True, null=True, help_text="説明圖片內容")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "旅程照片"
        verbose_name_plural = "旅程照片列表"
    
    def __str__(self):
        return f"{self.journey.title} - 照片"