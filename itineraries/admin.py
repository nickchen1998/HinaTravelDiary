from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django import forms
from django.core.exceptions import ValidationError
from .models import Itinerary, ItineraryPhoto, Location, LocationPhoto
from .utils import update_location_from_google_maps


class ItineraryForm(forms.ModelForm):
    """自定義行程表單，限制日期範圍"""
    
    class Meta:
        model = Itinerary
        fields = '__all__'
    
    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        journey = self.cleaned_data.get('journey')
        
        if start_date and journey:
            if start_date < journey.start_date or start_date > journey.end_date:
                raise ValidationError(
                    f'行程開始日期必須在旅程期間內 ({journey.start_date} 到 {journey.end_date})'
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
    fields = ['name', 'google_maps_url', 'order']
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
    readonly_fields = ['created_at', 'start_date', 'journey']

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

    def save_formset(self, request, form, formset, change):
        """
        處理 Inline formset 的儲存，包括地點的 Google Maps URL 更新和刪除操作
        """
        # 檢查是否為 LocationInline 的 formset
        if formset.model == Location:
            # 處理刪除的物件
            if hasattr(formset, 'deleted_objects'):
                for obj in formset.deleted_objects:
                    messages.info(request, f"🗑️ 已刪除地點「{obj.name}」")

            # 儲存新增和修改的物件
            instances = formset.save(commit=False)

            for instance in instances:
                # 檢查是否為新增的物件（沒有 pk）
                is_new = instance.pk is None

                # 先儲存實例
                instance.save()

                # 只有新增的地點且有 Google Maps URL 才更新資訊
                if is_new and instance.google_maps_url:
                    try:
                        success = update_location_from_google_maps(instance, instance.google_maps_url)
                        if success:
                            messages.success(
                                request,
                                f"✅ 成功新增地點「{instance.name}」並從 Google Maps 獲取詳細資訊！"
                            )
                        else:
                            messages.info(
                                request,
                                f"ℹ️ 已新增地點「{instance.name}」，但無法從 Google Maps 獲取額外資訊。"
                            )
                    except Exception as e:
                        messages.warning(
                            request,
                            f"⚠️ 更新地點「{instance.name}」資訊時發生錯誤: {str(e)}"
                        )
                elif is_new:
                    # 新增的地點但沒有 Google Maps URL
                    messages.success(request, f"✅ 成功新增地點「{instance.name}」")
                else:
                    # 修改現有地點（不觸發 Google Maps 更新）
                    messages.success(request, f"✅ 成功更新地點「{instance.name}」")

            # 儲存多對多關係和執行實際刪除
            formset.save_m2m()
        else:
            # 其他 formset 使用預設處理
            super().save_formset(request, form, formset, change)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['itinerary', 'name', 'address', 'order']
    list_filter = ['itinerary__journey__title',]
    search_fields = ['itinerary__title', ]
    ordering = ['itinerary', 'order']
    inlines = [LocationPhotoInline]
    list_per_page = 20
    list_editable = ['order']

    search_help_text = "請輸入行程名稱並搭配右側的旅程名稱來進行過濾。"

    fieldsets = (
        ('基本資訊', {
            'fields': ('itinerary', 'name', 'description', 'google_maps_url', 'order'),
            'description': '📝 輸入地點名稱和描述<br/>🔗 Google Maps 網址在建立後無法修改'
        }),
        ('自動填入資訊', {
            'fields': ('address', 'rating', 'place_types'),
            'description': '🤖 這些欄位會在儲存時自動從 Google Maps 獲取',
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """根據是否為新增物件來決定唯讀欄位"""
        readonly = ['address', 'rating', 'place_types']
        
        # 如果是編輯現有物件（obj 存在），則將 google_maps_url 設為唯讀
        if obj:
            readonly.append('google_maps_url')
        
        return readonly

    def save_model(self, request, obj, form, change):
        """
        覆寫 save_model 方法來處理 Google Maps URL 更新
        """
        # 先儲存基本資料
        super().save_model(request, obj, form, change)

        # 只在新增時處理 Google Maps URL
        if obj.google_maps_url and not change:
            try:
                success = update_location_from_google_maps(obj, obj.google_maps_url)
                if success:
                    messages.success(
                        request,
                        f"✅ 成功從 Google Maps 更新地點「{obj.name}」的資訊！"
                    )
                else:
                    messages.info(
                        request,
                        f"ℹ️ 無法從 Google Maps URL 獲取額外資訊，但地點已儲存。"
                    )
            except Exception as e:
                messages.warning(
                    request,
                    f"⚠️ 更新地點資訊時發生錯誤: {str(e)}，但地點已儲存。"
                )
