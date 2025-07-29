from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from django.db.models import F
from journeys.models import Journey
from .models import Itinerary, Location, LocationPhoto
from .utils import LocationHandler


def itinerary_list(request, journey_id):
    journey = get_object_or_404(Journey, id=journey_id)
    itineraries = Itinerary.objects.filter(journey=journey).order_by('start_date')
    
    context = {
        'journey': journey,
        'itineraries': itineraries,
    }
    return render(request, 'itineraries.html', context)


def location_list(request, itinerary_id):
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    locations = Location.objects.filter(itinerary=itinerary).order_by('order')
    
    context = {
        'itinerary': itinerary,
        'locations': locations,
    }
    return render(request, 'locations.html', context)


@require_GET
def location_map_data(request, itinerary_id):
    """提供地圖資料的 API endpoint"""
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    locations = Location.objects.filter(itinerary=itinerary).order_by('order')
    
    # 只返回有座標的地點
    location_data = []
    for location in locations:
        if location.latitude and location.longitude:
            location_data.append({
                'name': location.name,
                'description': location.description or '',
                'address': location.address or '',
                'rating': location.rating,
                'order': location.order,
                'lat': float(location.latitude),
                'lng': float(location.longitude),
                'url': location.google_maps_url or ''
            })
    
    return JsonResponse({
        'locations': location_data,
        'api_key': getattr(settings, 'GOOGLE_MAPS_API_KEY', ''),
        'itinerary_title': itinerary.title
    })


@require_http_methods(["POST"])
def create_location(request, itinerary_id):
    """建立新地點"""
    try:
        itinerary = get_object_or_404(Itinerary, id=itinerary_id)
        
        # 獲取表單數據
        name = request.POST.get('name')
        address = request.POST.get('address')
        google_maps_url = request.POST.get('google_maps_url')
        description = request.POST.get('description', '')
        arrived_hour = request.POST.get('arrived_hour')
        arrived_minute = request.POST.get('arrived_minute')
        departure_hour = request.POST.get('departure_hour')
        departure_minute = request.POST.get('departure_minute')
        
        # 驗證必填欄位
        if not all([name, address, google_maps_url]):
            return JsonResponse({'error': '請填寫所有必填欄位'}, status=400)
        
        # 計算新地點的順序（最大值+1）
        max_order = Location.objects.filter(itinerary=itinerary).aggregate(
            max_order=models.Max('order')
        )['max_order'] or 0
        
        # 建立地點
        location = Location.objects.create(
            itinerary=itinerary,
            name=name,
            address=address,
            google_maps_url=google_maps_url,
            description=description,
            order=max_order + 1
        )
        
        # 設定時間（如果有提供）
        if arrived_hour and arrived_minute:
            location.arrived_hour = int(arrived_hour)
            location.arrived_minute = int(arrived_minute)
        if departure_hour and departure_minute:
            location.departure_hour = int(departure_hour)
            location.departure_minute = int(departure_minute)
        
        # 使用 LocationHandler 自動填入經緯度、評分等資訊
        handler = LocationHandler()
        handler.update_location_from_google_maps(location, google_maps_url)
        
        # 處理照片上傳（最多3張）
        for i in range(3):
            image = request.FILES.get(f'image_{i}')
            if image:
                LocationPhoto.objects.create(
                    location=location,
                    image=image,
                    caption=request.POST.get(f'caption_{i}', '')
                )
        
        return JsonResponse({
            'success': True,
            'message': f'地點「{location.name}」建立成功！'
        })
        
    except Exception as e:
        return JsonResponse({'error': f'建立地點時發生錯誤：{str(e)}'}, status=500)


@require_http_methods(["POST"])
def edit_location(request, itinerary_id, location_id):
    """編輯地點"""
    try:
        itinerary = get_object_or_404(Itinerary, id=itinerary_id)
        location = get_object_or_404(Location, id=location_id, itinerary=itinerary)
        
        # 獲取表單數據（編輯時只能修改到達和離開時間）
        arrived_hour = request.POST.get('arrived_hour')
        arrived_minute = request.POST.get('arrived_minute')
        departure_hour = request.POST.get('departure_hour')
        departure_minute = request.POST.get('departure_minute')
        
        # 更新時間
        if arrived_hour and arrived_minute:
            location.arrived_hour = int(arrived_hour)
            location.arrived_minute = int(arrived_minute)
        else:
            location.arrived_hour = None
            location.arrived_minute = None
            
        if departure_hour and departure_minute:
            location.departure_hour = int(departure_hour)
            location.departure_minute = int(departure_minute)
        else:
            location.departure_hour = None
            location.departure_minute = None
        
        location.save()
        
        # 處理照片上傳（最多3張）
        existing_photos = location.locationphoto_set.count()
        
        for i in range(3):
            image = request.FILES.get(f'image_{i}')
            if image and existing_photos + i < 3:
                LocationPhoto.objects.create(
                    location=location,
                    image=image,
                    caption=request.POST.get(f'caption_{i}', '')
                )
        
        return JsonResponse({
            'success': True,
            'message': f'地點「{location.name}」更新成功！'
        })
        
    except Exception as e:
        return JsonResponse({'error': f'更新地點時發生錯誤：{str(e)}'}, status=500)


@require_http_methods(["DELETE"])
def delete_location(request, itinerary_id, location_id):
    """刪除地點"""
    try:
        itinerary = get_object_or_404(Itinerary, id=itinerary_id)
        location = get_object_or_404(Location, id=location_id, itinerary=itinerary)
        
        location_name = location.name
        deleted_order = location.order
        
        # 刪除地點
        location.delete()
        
        # 重新排序剩餘地點
        Location.objects.filter(
            itinerary=itinerary,
            order__gt=deleted_order
        ).update(order=F('order') - 1)
        
        return JsonResponse({
            'success': True,
            'message': f'地點「{location_name}」已刪除'
        })
        
    except Exception as e:
        return JsonResponse({'error': f'刪除地點時發生錯誤：{str(e)}'}, status=500)


@require_http_methods(["POST"])
def move_location(request, itinerary_id, location_id):
    """移動地點順序"""
    try:
        itinerary = get_object_or_404(Itinerary, id=itinerary_id)
        location = get_object_or_404(Location, id=location_id, itinerary=itinerary)
        
        direction = request.POST.get('direction')
        if direction not in ['up', 'down']:
            return JsonResponse({'error': '無效的移動方向'}, status=400)
        
        current_order = location.order
        
        if direction == 'up' and current_order > 1:
            # 向上移動
            other_location = Location.objects.get(
                itinerary=itinerary,
                order=current_order - 1
            )
            location.order = current_order - 1
            other_location.order = current_order
            location.save()
            other_location.save()
            
        elif direction == 'down':
            # 向下移動
            max_order = Location.objects.filter(itinerary=itinerary).aggregate(
                max_order=models.Max('order')
            )['max_order']
            
            if current_order < max_order:
                other_location = Location.objects.get(
                    itinerary=itinerary,
                    order=current_order + 1
                )
                location.order = current_order + 1
                other_location.order = current_order
                location.save()
                other_location.save()
        
        return JsonResponse({
            'success': True,
            'message': '地點順序已更新'
        })
        
    except Exception as e:
        return JsonResponse({'error': f'移動地點時發生錯誤：{str(e)}'}, status=500)
