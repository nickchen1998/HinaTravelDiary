import re
import requests
import json
import logging
from typing import List, Dict, Optional, Tuple
from django.conf import settings
import urllib.parse
from urllib.parse import urlparse, parse_qs
import time

# 設定日誌
logger = logging.getLogger(__name__)


class GoogleMapsParser:
    """
    增強版 Google Maps URL 解析器
    支援多種 Google Maps URL 格式並整合多個 Google API
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None)
        self.session = requests.Session()
        
    def _make_api_request(self, url: str, params: Dict) -> Optional[Dict]:
        """
        統一的 API 請求處理器
        """
        if not self.api_key:
            logger.warning("Google Maps API Key 未設定")
            return None
            
        params['key'] = self.api_key
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'OK':
                return data
            else:
                logger.error(f"Google API 錯誤: {data.get('status')} - {data.get('error_message', '')}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API 請求失敗: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失敗: {e}")
            return None
    
    def extract_coordinates_from_url(self, url: str) -> Optional[Tuple[float, float]]:
        """
        從各種 Google Maps URL 格式中提取座標
        支援更多格式的 URL
        """
        # 清理 URL
        url = url.strip()
        
        # 模式 1: /@lat,lng,zoom 格式
        coord_patterns = [
            r'/@(-?\d+\.?\d*),(-?\d+\.?\d*),\d+\.?\d*z',
            r'/@(-?\d+\.?\d*),(-?\d+\.?\d*)',
            r'!3d(-?\d+\.?\d*)!4d(-?\d+\.?\d*)',
            r'q=(-?\d+\.?\d*),(-?\d+\.?\d*)',
            r'center=(-?\d+\.?\d*),(-?\d+\.?\d*)',
            r'll=(-?\d+\.?\d*),(-?\d+\.?\d*)',
        ]
        
        for pattern in coord_patterns:
            match = re.search(pattern, url)
            if match:
                try:
                    lat = float(match.group(1))
                    lng = float(match.group(2))
                    if -90 <= lat <= 90 and -180 <= lng <= 180:
                        return (lat, lng)
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def extract_place_id_from_url(self, url: str) -> Optional[str]:
        """
        從 Google Maps URL 中提取 place_id
        """
        place_id_patterns = [
            r'place_id=([A-Za-z0-9_-]+)',
            r'ftid=([A-Za-z0-9_-]+)',
            r'!1s([A-Za-z0-9_-]+)',
        ]
        
        for pattern in place_id_patterns:
            match = re.search(pattern, url)
            if match:
                place_id = match.group(1)
                # 確保 place_id 格式正確（不包含 0x 格式）
                if not place_id.startswith('0x'):
                    return place_id
        
        return None
    
    def search_place_by_query(self, query: str) -> Optional[Dict]:
        """
        使用 Google Places Text Search API 搜尋地點
        """
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            'query': query,
            'language': 'zh-TW',
            'region': 'tw',
            'fields': 'place_id,name,formatted_address,rating,user_ratings_total,types,geometry'
        }
        
        data = self._make_api_request(url, params)
        if data and data.get('results'):
            result = data['results'][0]
            # 如果有 place_id，獲取詳細資訊
            if result.get('place_id'):
                detailed_result = self.get_place_details(result['place_id'])
                if detailed_result:
                    return detailed_result
            return result
        
        return None
    
    def get_place_details(self, place_id: str) -> Optional[Dict]:
        """
        使用 Google Places Details API 獲取地點詳細資訊
        """
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            'place_id': place_id,
            'fields': 'name,formatted_address,geometry,rating,user_ratings_total,types,photos,opening_hours',
            'language': 'zh-TW'
        }
        
        data = self._make_api_request(url, params)
        if data and data.get('result'):
            return data['result']
        
        return None
    
    def geocode_address(self, address: str) -> Optional[Tuple[float, float, str]]:
        """
        地址轉座標
        返回 (lat, lng, formatted_address)
        """
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'address': address,
            'language': 'zh-TW',
            'region': 'tw'
        }
        
        data = self._make_api_request(url, params)
        if data and data.get('results'):
            result = data['results'][0]
            location = result['geometry']['location']
            return (
                location['lat'], 
                location['lng'], 
                result['formatted_address']
            )
        
        return None
    
    def reverse_geocode(self, lat: float, lng: float) -> Optional[str]:
        """
        座標轉地址
        """
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'latlng': f"{lat},{lng}",
            'language': 'zh-TW'
        }
        
        data = self._make_api_request(url, params)
        if data and data.get('results'):
            return data['results'][0]['formatted_address']
        
        return None
    
    def resolve_short_url(self, short_url: str) -> Optional[str]:
        """
        解析短網址獲取完整 URL
        """
        try:
            response = self.session.head(short_url, allow_redirects=True, timeout=10)
            return response.url
        except requests.exceptions.RequestException as e:
            logger.error(f"短網址解析失敗: {e}")
            return None
    
    def extract_search_query_from_url(self, url: str) -> Optional[str]:
        """
        從 Google Maps URL 中提取搜尋查詢字串
        """
        # 解析 URL 參數
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        # 檢查各種可能的查詢參數
        query_params = ['q', 'query', 'search']
        for param in query_params:
            if param in params and params[param]:
                return params[param][0]
        
        # 從路徑中提取
        path_patterns = [
            r'/search/([^/]+)',
            r'/place/([^/]+)',
        ]
        
        for pattern in path_patterns:
            match = re.search(pattern, url)
            if match:
                return urllib.parse.unquote(match.group(1))
        
        return None
    
    def parse_my_maps_url(self, url: str) -> List[Dict]:
        """
        解析 Google My Maps 分享連結
        這個功能需要特殊處理，因為 My Maps 沒有公開 API
        """
        locations = []
        
        # 提取地圖 ID
        map_id_match = re.search(r'mid=([A-Za-z0-9_-]+)', url)
        if not map_id_match:
            return locations
        
        map_id = map_id_match.group(1)
        
        # 嘗試從 URL 中提取更多資訊
        # 注意：這是一個基本實作，實際的 My Maps 解析可能需要更複雜的處理
        
        try:
            # 嘗試獲取地圖頁面內容
            response = self.session.get(url, timeout=10)
            content = response.text
            
            # 使用正則表達式尋找可能的座標資訊
            coord_matches = re.findall(r'[-]?\d+\.\d+,[-]?\d+\.\d+', content)
            
            for i, coord_str in enumerate(coord_matches[:10]):  # 限制最多 10 個地點
                try:
                    coords = coord_str.split(',')
                    if len(coords) == 2:
                        lat, lng = float(coords[0]), float(coords[1])
                        if -90 <= lat <= 90 and -180 <= lng <= 180:
                            address = self.reverse_geocode(lat, lng)
                            locations.append({
                                'name': address or f"My Maps 地點 {i+1}",
                                'description': f'從 Google My Maps 匯入的地點',
                                'address': address,
                                'order': i + 1
                            })
                except ValueError:
                    continue
                    
        except requests.exceptions.RequestException as e:
            logger.error(f"無法存取 My Maps URL: {e}")
        
        return locations
    
    def parse_google_maps_url(self, url: str) -> List[Dict]:
        """
        主要的 Google Maps URL 解析函數
        """
        locations = []
        original_url = url
        
        # 首先解析短網址
        if 'maps.app.goo.gl' in url or 'goo.gl' in url:
            resolved_url = self.resolve_short_url(url)
            if resolved_url:
                url = resolved_url
        
        # 方法 1: 優先嘗試提取搜尋查詢（最準確）
        search_query = self.extract_search_query_from_url(url)
        if search_query:
            # 清理搜尋查詢中的 + 符號
            clean_query = search_query.replace('+', ' ')
            logger.info(f"使用搜尋查詢: {clean_query}")
            
            place_result = self.search_place_by_query(clean_query)
            if place_result:
                location = self._create_location_from_search_result(place_result, original_url)
                if location:
                    locations.append(location)
                    return locations
        
        # 方法 2: 嘗試提取 place_id
        place_id = self.extract_place_id_from_url(url)
        if place_id:
            logger.info(f"使用 place_id: {place_id}")
            place_details = self.get_place_details(place_id)
            if place_details:
                location = self._create_location_from_place_details(place_details, original_url)
                if location:
                    locations.append(location)
                    return locations
        
        # 方法 3: 嘗試提取座標（最後手段）
        coordinates = self.extract_coordinates_from_url(url)
        if coordinates:
            lat, lng = coordinates
            address = self.reverse_geocode(lat, lng)
            
            location = {
                'name': address or f"地點 ({lat:.6f}, {lng:.6f})",
                'description': f'從 Google Maps 座標匯入: {original_url}',
                'address': address,
                'latitude': lat,
                'longitude': lng,
                'order': 1
            }
            
            locations.append(location)
            return locations
        
        # 方法 4: 如果是 My Maps，使用特殊處理
        if 'maps/d/' in url:
            return self.parse_my_maps_url(url)
        
        return locations
    
    def _create_location_from_place_details(self, place_details: Dict, source_url: str) -> Optional[Dict]:
        """
        從 Google Places 詳細資訊創建地點物件
        """
        try:
            geometry = place_details.get('geometry', {})
            location_data = geometry.get('location', {})
            
            if not location_data:
                return None
            
            # 構建描述
            description_parts = [f'從 Google Maps 匯入: {source_url}']
            
            if place_details.get('rating'):
                description_parts.append(f"評分: {place_details['rating']}")
            
            if place_details.get('user_ratings_total'):
                description_parts.append(f"評論數: {place_details['user_ratings_total']}")
            
            types_zh = []
            if place_details.get('types'):
                types_zh = self._translate_place_types(place_details['types'])
                if types_zh:
                    description_parts.append(f"類型: {', '.join(types_zh)}")
            
            return {
                'name': place_details.get('name', '未知地點'),
                'description': '\n'.join(description_parts),
                'address': place_details.get('formatted_address'),
                'latitude': location_data.get('lat'),
                'longitude': location_data.get('lng'),
                'rating': place_details.get('rating'),
                'place_types': ', '.join(types_zh) if types_zh else None,
                'order': 1
            }
            
        except (KeyError, TypeError, ValueError) as e:
            logger.error(f"創建地點物件時發生錯誤: {e}")
            return None
    
    def _create_location_from_search_result(self, search_result: Dict, source_url: str) -> Optional[Dict]:
        """
        從 Google Places 搜尋結果創建地點物件
        """
        try:
            geometry = search_result.get('geometry', {})
            location_data = geometry.get('location', {})
            
            if not location_data:
                return None
            
            description_parts = [f'從 Google Maps 搜尋匯入: {source_url}']
            
            if search_result.get('rating'):
                description_parts.append(f"評分: {search_result['rating']}")
            
            if search_result.get('formatted_address'):
                description_parts.append(f"地址: {search_result['formatted_address']}")
            
            # 獲取地點類型
            types_zh = self._translate_place_types(search_result.get('types', []))
            
            return {
                'name': search_result.get('name', '未知地點'),
                'description': '\n'.join(description_parts),
                'address': search_result.get('formatted_address'),
                'latitude': location_data.get('lat'),
                'longitude': location_data.get('lng'),
                'rating': search_result.get('rating'),
                'place_types': ', '.join(types_zh) if types_zh else None,
                'order': 1
            }
            
        except (KeyError, TypeError, ValueError) as e:
            logger.error(f"創建搜尋結果地點物件時發生錯誤: {e}")
            return None
    
    def _translate_place_types(self, types: List[str]) -> List[str]:
        """
        將 Google Places 類型翻譯成中文
        """
        type_mapping = {
            'restaurant': '餐廳',
            'tourist_attraction': '旅遊景點',
            'lodging': '住宿',
            'shopping_mall': '購物中心',
            'park': '公園',
            'museum': '博物館',
            'amusement_park': '遊樂園',
            'zoo': '動物園',
            'aquarium': '水族館',
            'temple': '寺廟',
            'church': '教堂',
            'mosque': '清真寺',
            'hospital': '醫院',
            'pharmacy': '藥局',
            'gas_station': '加油站',
            'bank': '銀行',
            'atm': 'ATM',
            'convenience_store': '便利商店',
            'supermarket': '超市',
            'bakery': '麵包店',
            'cafe': '咖啡店',
            'bar': '酒吧',
            'night_club': '夜店',
            'gym': '健身房',
            'spa': 'SPA',
            'beauty_salon': '美容院',
            'movie_theater': '電影院',
            'library': '圖書館',
            'school': '學校',
            'university': '大學',
            'store': '商店',
            'point_of_interest': '景點',
            'establishment': '店家',
        }
        
        translated = []
        for place_type in types[:3]:  # 只取前 3 個類型
            if place_type in type_mapping:
                translated.append(type_mapping[place_type])
        
        return translated


def import_locations_from_google_maps(url: str) -> List[Dict]:
    """
    主要匯入函數：從 Google Maps URL 匯入地點
    使用增強版解析器提供最佳體驗
    """
    if not url:
        return []
    
    parser = GoogleMapsParser()
    
    try:
        locations = parser.parse_google_maps_url(url)
        
        if not locations:
            # 如果無法解析，創建一個提示地點
            locations = [{
                'name': '無法解析的 Google Maps 連結',
                'description': f'無法從此 URL 解析地點資訊: {url}\n\n請檢查連結格式或手動編輯地點資訊。',
                'order': 1,
                'google_maps_url': url
            }]
        
        logger.info(f"成功解析 {len(locations)} 個地點")
        return locations
        
    except Exception as e:
        logger.error(f"解析 Google Maps URL 時發生未預期錯誤: {e}")
        return [{
            'name': 'Google Maps 匯入錯誤',
            'description': f'解析時發生錯誤: {str(e)}\n\nURL: {url}',
            'order': 1,
            'google_maps_url': url
        }]


def import_locations_from_multiple_urls(urls_text: str) -> List[Dict]:
    """
    從多個 Google Maps URL 批次匯入地點
    """
    if not urls_text:
        return []
    
    # 分割 URLs，過濾空行
    urls = [url.strip() for url in urls_text.strip().split('\n') if url.strip()]
    
    all_locations = []
    parser = GoogleMapsParser()
    
    for i, url in enumerate(urls):
        try:
            logger.info(f"正在處理第 {i+1}/{len(urls)} 個網址: {url}")
            locations = parser.parse_google_maps_url(url)
            
            if locations:
                for location in locations:
                    location['order'] = i + 1
                    location['google_maps_url'] = url
                all_locations.extend(locations)
            else:
                # 如果無法解析，仍然創建一個地點記錄
                all_locations.append({
                    'name': f'待解析地點 {i+1}',
                    'description': f'無法自動解析的 Google Maps 連結\n\nURL: {url}',
                    'order': i + 1,
                    'google_maps_url': url
                })
                
        except Exception as e:
            logger.error(f"處理 URL {url} 時發生錯誤: {e}")
            all_locations.append({
                'name': f'錯誤地點 {i+1}',
                'description': f'處理時發生錯誤: {str(e)}\n\nURL: {url}',
                'order': i + 1,
                'google_maps_url': url
            })
    
    logger.info(f"批次處理完成，共創建 {len(all_locations)} 個地點")
    return all_locations


def update_location_from_google_maps(location, url: str) -> bool:
    """
    使用 Google Maps URL 更新地點資訊
    """
    if not url:
        return False
    
    parser = GoogleMapsParser()
    
    try:
        locations = parser.parse_google_maps_url(url)
        
        if locations:
            location_data = locations[0]  # 取第一個結果
            
            # 更新地點資訊（只更新有值的欄位）
            if location_data.get('address'):
                location.address = location_data['address']
            
            if location_data.get('latitude'):
                location.latitude = location_data['latitude']
            
            if location_data.get('longitude'):
                location.longitude = location_data['longitude']
            
            if location_data.get('rating'):
                location.rating = location_data['rating']
            
            if location_data.get('place_types'):
                location.place_types = location_data['place_types']
            
            # 總是更新 URL
            location.google_maps_url = url
            
            # 儲存變更
            location.save()
            
            logger.info(f"成功更新地點資訊: {location.name}")
            return True
        
    except Exception as e:
        logger.error(f"更新地點資訊時發生錯誤: {e}")
    
    return False