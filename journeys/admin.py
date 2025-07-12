from django.contrib import admin
from django.utils.html import format_html
from .models import Country, City, Journey, JourneyPhoto


class JourneyPhotoInline(admin.StackedInline):
    model = JourneyPhoto
    extra = 0
    max_num = 1
    readonly_fields = ['created_at', 'image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 200px; height: 200px; object-fit: cover; border-radius: 8px;" />', obj.image.url)
        return '尚未上傳圖片'
    image_preview.short_description = '圖片預覽'


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'english_name', 'country_code', 'is_highlighted']
    search_fields = ['name', 'english_name', 'country_code']
    list_filter = ['is_highlighted']
    list_editable = ['is_highlighted']


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'english_name', 'country']
    list_filter = ['country']
    search_fields = ['name', 'english_name', 'country__name']


@admin.register(Journey)
class JourneyAdmin(admin.ModelAdmin):
    list_display = ['title', 'country', 'start_date', 'end_date', 'is_highlighted', 'has_photo', 'created_at']
    list_filter = ['country', 'is_highlighted', 'start_date', 'end_date', 'created_at']
    search_fields = ['title', 'description', 'country__name']
    date_hierarchy = 'start_date'
    inlines = [JourneyPhotoInline]
    list_editable = ['is_highlighted']
    list_per_page = 20
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('title', 'country', 'description')
        }),
        ('日期', {
            'fields': ('start_date', 'end_date')
        }),
        ('設定', {
            'fields': ('is_highlighted',)
        }),
    )
    
    def has_photo(self, obj):
        return hasattr(obj, 'journeyphoto') and obj.journeyphoto is not None
    has_photo.boolean = True
    has_photo.short_description = '有照片'


