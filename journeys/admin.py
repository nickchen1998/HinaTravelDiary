from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from datetime import timedelta
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
            'fields': ('title', 'country', 'city', 'description')
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
    
    def save_model(self, request, obj, form, change):
        """儲存旅程並自動建立行程"""
        # 先儲存旅程
        super().save_model(request, obj, form, change)
        
        # 只有在新建旅程時才自動建立行程
        if not change:
            self.create_itineraries_for_journey(request, obj)
    
    def create_itineraries_for_journey(self, request, journey):
        """為旅程自動建立每日行程"""
        from itineraries.models import Itinerary
        
        current_date = journey.start_date
        day_count = 1
        created_count = 0
        
        while current_date <= journey.end_date:
            # 格式化日期為 YYYY.MM.DD
            date_str = current_date.strftime('%Y.%m.%d')
            title = f"Day-{day_count:02d}-{date_str}"
            
            # 建立行程
            itinerary = Itinerary.objects.create(
                journey=journey,
                title=title,
                description=f"第 {day_count} 天行程",
                start_date=current_date
            )
            
            created_count += 1
            current_date += timedelta(days=1)
            day_count += 1
        
        # 顯示成功訊息
        messages.success(
            request,
            f"✅ 已成功為旅程「{journey.title}」自動建立 {created_count} 個行程！"
        )


