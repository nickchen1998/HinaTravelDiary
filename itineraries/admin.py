from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django import forms
from django.core.exceptions import ValidationError
from .models import Itinerary, ItineraryPhoto, Location, LocationPhoto


class ItineraryForm(forms.ModelForm):
    """自定義行程表單，限制日期範圍"""
    
    class Meta:
        model = Itinerary
        fields = '__all__'
    
    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        journey = self.cleaned_data.get('journey')
        
        if start_date and journey:
            # 檢查日期是否在旅程起迄日範圍內
            if start_date < journey.start_date or start_date > journey.end_date:
                raise ValidationError(
                    f'行程開始日期必須在旅程期間內 ({journey.start_date} 到 {journey.end_date})'
                )
            
            # 檢查該日期是否已經存在於該旅程的其他行程中
            existing_itineraries = Itinerary.objects.filter(
                journey=journey,
                start_date=start_date
            )
            
            # 如果是編輯現有行程，排除自己
            if self.instance and self.instance.pk:
                existing_itineraries = existing_itineraries.exclude(pk=self.instance.pk)
            
            if existing_itineraries.exists():
                existing_itinerary = existing_itineraries.first()
                raise ValidationError(
                    f'該日期已被行程「{existing_itinerary.title}」使用，請選擇其他日期'
                )
        
        return start_date


class ItineraryPhotoInline(admin.StackedInline):
    model = ItineraryPhoto
    extra = 0
    max_num = 1
    readonly_fields = ['created_at', 'image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 200px; height: 200px; object-fit: cover; border-radius: 8px;" />',
                obj.image.url)
        return '尚未上傳圖片'

    image_preview.short_description = '圖片預覽'


class LocationPhotoInline(admin.TabularInline):
    model = LocationPhoto
    extra = 0
    max_num = 3
    readonly_fields = ['created_at', 'image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 4px;" />',
                obj.image.url)
        return '尚未上傳圖片'

    image_preview.short_description = '圖片預覽'


class LocationInline(admin.TabularInline):
    model = Location
    extra = 1
    fields = ['name', 'address', 'google_maps_url']
    ordering = ['order']
    can_delete = True


@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
    form = ItineraryForm
    list_display = ['title', 'journey', 'start_date', 'location_count', 'has_photo', 'created_at']
    list_filter = ['journey__title', ]
    ordering = ['start_date']
    inlines = [ItineraryPhotoInline, LocationInline]
    list_per_page = 20
    readonly_fields = ['created_at',]

    fieldsets = (
        ('基本資訊', {
            'fields': ('journey', 'title', 'description')
        }),
        ('日期', {
            'fields': ('start_date',)
        }),
    )

    def location_count(self, obj):
        return obj.location_set.count()

    location_count.short_description = '地點數量'

    def has_photo(self, obj):
        return hasattr(obj, 'itineraryphoto') and obj.itineraryphoto is not None

    has_photo.boolean = True
    has_photo.short_description = '有照片'


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['itinerary', 'name', 'address', 'order', 'arrived_hour', 'arrived_minute']
    list_filter = ['itinerary__journey__title',]
    search_fields = ['itinerary__title', ]
    ordering = ['itinerary', 'order']
    inlines = [LocationPhotoInline]
    list_per_page = 20
    list_editable = ['order', 'arrived_hour', 'arrived_minute']

    search_help_text = "請輸入行程名稱並搭配右側的旅程名稱來進行過濾。"

    fieldsets = (
        ('基本資訊', {
            'fields': ('itinerary', 'name', 'description', 'google_maps_url', 'order'),
            'description': '📝 輸入地點名稱、描述和相關網址'
        }),
        ('時間資訊', {
            'fields': ('arrived_hour', 'arrived_minute'),
            'description': '⏰ 到達時間（小時和分鐘）'
        }),
        ('地點資訊', {
            'fields': ('address', 'latitude', 'longitude', 'rating', 'place_types'),
            'description': '📍 地點的詳細資訊（可手動輸入或由系統自動填入）',
            'classes': ('collapse',)
        }),
    )

