"""
Django 信號處理器
用於在 Location 被 post_save 時自動更新地點資訊
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Location
from .utils import LocationHandler

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Location)
def update_location_info_on_save(sender, instance, created, **kwargs):
    """
    Location post_save 信號處理器
    
    當 Location 被儲存時：
    1. 如果是新建的地點且有地點名稱，會自動搜尋星等、景點類別等資訊
    2. 如果有地址但沒有座標，會自動進行地址編碼獲取緯度經度
    3. 使用 update 方式更新，避免觸發額外的 post_save 信號
    """
    # 避免無限遞迴，如果是透過 update 觸發的就不處理
    if hasattr(instance, '_updating_from_signal'):
        return

    # if created and not instance.order:
    #     Location.objects.filter(pk=instance.pk).update(**{
    #         "order": instance.itinerary.location_set.count(),
    #     })
    
    try:
        handler = LocationHandler()
        
        # 標記正在更新，避免無限遞迴
        instance._updating_from_signal = True
        
        # 檢查是否需要更新資訊
        needs_update = False
        update_fields = []
        
        # 如果有地點名稱但缺少評分或類型資訊，進行搜尋
        if instance.name and (not instance.rating or not instance.place_types):
            location_info = handler.search_location_info(instance.name)
            if location_info:
                # 只更新空白的欄位
                if not instance.rating and location_info.get('rating'):
                    instance.rating = location_info['rating']
                    update_fields.append('rating')
                    needs_update = True
                
                if not instance.place_types and location_info.get('place_types'):
                    instance.place_types = location_info['place_types']
                    update_fields.append('place_types')
                    needs_update = True
                
                # 如果沒有地址資訊，使用搜尋結果的地址
                if not instance.address and location_info.get('address'):
                    instance.address = location_info['address']
                    update_fields.append('address')
                    needs_update = True
                
                if not instance.latitude and location_info.get('latitude'):
                    instance.latitude = location_info['latitude']
                    update_fields.append('latitude')
                    needs_update = True
                
                if not instance.longitude and location_info.get('longitude'):
                    instance.longitude = location_info['longitude']
                    update_fields.append('longitude')
                    needs_update = True
        
        # 如果有地址但沒有座標，進行地址編碼
        if instance.address and (not instance.latitude or not instance.longitude):
            address_info = handler.update_location_by_address(instance.address)
            if address_info:
                instance.address = address_info['address']  # 使用格式化後的地址
                instance.latitude = address_info['latitude']
                instance.longitude = address_info['longitude']
                
                update_fields.extend(['address', 'latitude', 'longitude'])
                needs_update = True
        
        # 使用 update 方式更新，避免觸發額外的 post_save 信號
        if needs_update:
            Location.objects.filter(pk=instance.pk).update(**{
                field: getattr(instance, field) for field in update_fields
            })
            
            logger.info(f"自動更新地點資訊: {instance.name} - 更新欄位: {', '.join(update_fields)}")
    
    except Exception as e:
        logger.error(f"更新地點資訊時發生錯誤: {e}")
    
    finally:
        # 清除標記
        if hasattr(instance, '_updating_from_signal'):
            delattr(instance, '_updating_from_signal')