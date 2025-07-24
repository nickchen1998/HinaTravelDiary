from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from datetime import timedelta
from .models import Country, City, Journey, JourneyPhoto
from itineraries.models import Itinerary


def journey_list(request, country_id):
    """顯示特定國家的旅程列表"""
    country = get_object_or_404(Country, id=country_id)
    journeys = Journey.objects.filter(country=country).order_by('-start_date')
    
    # 為每個旅程計算行程數量
    for journey in journeys:
        journey.itinerary_count = Itinerary.objects.filter(journey=journey).count()
    
    context = {
        'country': country,
        'journeys': journeys,
    }
    return render(request, 'journeys.html', context)


@require_http_methods(["POST"])
def create_journey(request, country_id):
    """建立新旅程"""
    try:
        country = get_object_or_404(Country, id=country_id)
        
        # 獲取表單數據
        title = request.POST.get('title')
        description = request.POST.get('description')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        city_id = request.POST.get('city')
        image = request.FILES.get('image')
        
        # 驗證必填字段
        if not all([title, description, start_date, end_date]):
            return JsonResponse({'error': '請填寫所有必填字段'}, status=400)
        
        # 獲取城市（如果有選擇）
        city = None
        if city_id:
            try:
                city = City.objects.get(id=city_id, country=country)
            except City.DoesNotExist:
                return JsonResponse({'error': '所選城市不存在'}, status=400)
        
        # 建立旅程
        journey = Journey.objects.create(
            country=country,
            city=city,
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date
        )
        
        # 如果有上傳圖片，建立 JourneyPhoto
        if image:
            JourneyPhoto.objects.create(
                journey=journey,
                image=image
            )
        
        # 自動建立行程
        create_itineraries_for_journey(journey)
        
        return JsonResponse({
            'success': True,
            'message': f'旅程「{journey.title}」建立成功！'
        })
        
    except Exception as e:
        return JsonResponse({'error': f'建立旅程時發生錯誤：{str(e)}'}, status=500)


@require_http_methods(["POST"])
def edit_journey(request, country_id, journey_id):
    """編輯旅程"""
    try:
        country = get_object_or_404(Country, id=country_id)
        journey = get_object_or_404(Journey, id=journey_id, country=country)
        
        # 獲取表單數據
        title = request.POST.get('title')
        description = request.POST.get('description')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        city_id = request.POST.get('city')
        image = request.FILES.get('image')
        
        # 驗證必填字段
        if not all([title, description, start_date, end_date]):
            return JsonResponse({'error': '請填寫所有必填字段'}, status=400)
        
        # 獲取城市（如果有選擇）
        city = None
        if city_id:
            try:
                city = City.objects.get(id=city_id, country=country)
            except City.DoesNotExist:
                return JsonResponse({'error': '所選城市不存在'}, status=400)
        
        # 更新旅程
        journey.title = title
        journey.description = description
        journey.start_date = start_date
        journey.end_date = end_date
        journey.city = city
        journey.save()
        
        # 如果有上傳新圖片，更新 JourneyPhoto
        if image:
            # 刪除舊圖片（如果存在）
            if hasattr(journey, 'journeyphoto'):
                journey.journeyphoto.delete()
            
            # 建立新圖片
            JourneyPhoto.objects.create(
                journey=journey,
                image=image
            )
        
        return JsonResponse({
            'success': True,
            'message': f'旅程「{journey.title}」更新成功！'
        })
        
    except Exception as e:
        return JsonResponse({'error': f'更新旅程時發生錯誤：{str(e)}'}, status=500)


def create_itineraries_for_journey(journey):
    """為旅程自動建立每日行程"""
    current_date = journey.start_date
    day_count = 1
    created_count = 0
    
    while current_date <= journey.end_date:
        # 格式化日期為 YYYY.MM.DD
        date_str = current_date.strftime('%Y.%m.%d')
        title = f"Day-{day_count:02d}-{date_str}"
        
        # 建立行程
        Itinerary.objects.create(
            journey=journey,
            title=title,
            description=f"第 {day_count} 天行程",
            start_date=current_date
        )
        
        created_count += 1
        current_date += timedelta(days=1)
        day_count += 1
    
    return created_count
