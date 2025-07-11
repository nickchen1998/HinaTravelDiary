from django.contrib import admin
from django.utils.html import format_html
from .models import Itinerary, ItineraryPhoto, Location, LocationPhoto


class ItineraryPhotoInline(admin.StackedInline):
    model = ItineraryPhoto
    extra = 0
    max_num = 1
    readonly_fields = ['uuid', 'created_at', 'image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 200px; height: 200px; object-fit: cover; border-radius: 8px;" />', obj.image.url)
        return '尚未上傳圖片'
    image_preview.short_description = '圖片預覽'


class LocationPhotoInline(admin.TabularInline):
    model = LocationPhoto
    extra = 0
    readonly_fields = ['uuid', 'created_at', 'image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 4px;" />', obj.image.url)
        return '尚未上傳圖片'
    image_preview.short_description = '圖片預覽'


class LocationInline(admin.TabularInline):
    model = Location
    extra = 0
    fields = ['name', 'description', 'latitude', 'longitude', 'order']
    ordering = ['order']


@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
    list_display = ['title', 'journey', 'start_date', 'location_count', 'has_photo', 'created_at']
    list_filter = ['journey__country', 'start_date', 'created_at']
    search_fields = ['title', 'description', 'journey__title']
    date_hierarchy = 'start_date'
    inlines = [ItineraryPhotoInline, LocationInline]
    list_per_page = 20
    
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
    list_display = ['name', 'itinerary', 'order', 'latitude', 'longitude', 'photo_count', 'created_at']
    list_filter = ['itinerary__journey__country', 'created_at']
    search_fields = ['name', 'description', 'itinerary__title']
    ordering = ['itinerary', 'order']
    inlines = [LocationPhotoInline]
    list_per_page = 20
    list_editable = ['order']
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('itinerary', 'name', 'description', 'order')
        }),
        ('地理位置', {
            'fields': ('latitude', 'longitude')
        }),
    )
    
    def photo_count(self, obj):
        return obj.locationphoto_set.count()
    photo_count.short_description = '照片數量'


