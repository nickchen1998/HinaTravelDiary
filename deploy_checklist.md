# Hina Travel Diary - 部署檢查清單

## WhiteNoise 配置已完成 ✅

### 已配置的項目：

1. **安裝 WhiteNoise**
   ```bash
   poetry add whitenoise
   ```

2. **Middleware 配置**
   - 已在 `settings.py` 中添加 `whitenoise.middleware.WhiteNoiseMiddleware`
   - 位置正確（在 SecurityMiddleware 之後）

3. **靜態檔案配置**
   - `STATIC_URL = '/static/'`
   - `STATIC_ROOT = BASE_DIR / 'staticfiles'`
   - `STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'`

4. **Media 檔案配置**
   - 已在 `wsgi.py` 中配置 WhiteNoise 處理 media 檔案
   - 支援用戶上傳的圖片檔案

## 部署前準備

### 1. 收集靜態檔案
```bash
python manage.py collectstatic --noinput
```

### 2. 環境變數設定
請在部署平台設定以下環境變數：
- `SECRET_KEY`: Django 密鑰
- `DEBUG`: 設為 `False`
- `ALLOWED_HOSTS`: 您的網域名稱

### 3. 資料庫遷移
```bash
python manage.py migrate
```

### 4. 建立超級用戶
```bash
python manage.py createsuperuser
```

## 支援的部署平台

✅ **Heroku**
✅ **Railway** 
✅ **DigitalOcean App Platform**
✅ **Google Cloud Run**
✅ **AWS Elastic Beanstalk**

## 測試

在本地測試生產配置：
```bash
# 設定為生產模式
export DEBUG=False
python manage.py runserver
```

確認：
- 靜態檔案正常載入
- Media 檔案（上傳的圖片）正常顯示
- Admin 介面樣式正常