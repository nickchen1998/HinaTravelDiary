# TravelDiary 旅遊日記系統

一個使用 Django 開發的旅遊日記管理系統，讓使用者能夠記錄旅程、行程規劃和地點資訊。

## 功能特色

- **旅程管理 (Journeys)**：記錄每一次的旅行，包含國家、城市資訊
- **行程規劃 (Itineraries)**：為每個旅程建立詳細的日程安排
- **地點記錄 (Locations)**：記錄每個造訪的地點，包含經緯度、時間、描述等資訊
- **照片上傳**：支援上傳旅程和行程相關照片
- **使用者認證**：使用 Django-allauth 進行用戶管理

## 技術架構

- **後端框架**：Django 5.2.4
- **資料庫**：PostgreSQL with pgvector extension
- **Web 伺服器**：Nginx + Gunicorn
- **容器化**：Docker & Docker Compose
- **靜態檔案處理**：WhiteNoise
- **認證系統**：Django-allauth

## 專案結構

```
TravelDiary/
├── HinaTravelDiary/     # Django 專案設定
├── homepage/            # 首頁應用
├── journeys/            # 旅程管理應用
├── itineraries/         # 行程規劃應用
├── templates/           # HTML 模板
├── static/              # 靜態檔案
├── docker-compose.yml   # Docker Compose 設定
├── Dockerfile           # Docker 映像檔設定
├── nginx.conf           # Nginx 設定檔
└── pyproject.toml       # Python 專案依賴設定
```

## 部署方式

1. 環境變數設定：

    在專案根目錄下建立 `.env` 檔案，並設定以下環境變數：
    
    ```env
    DEBUG="True"
    GOOGLE_MAPS_API_KEY=""
    GOOGLE_OAUTH_CLIENT_ID=""
    GOOGLE_OAUTH_CLIENT_SECRET=""
    
    POSTGRES_VOLUME="" # 不要設定為專案跟目錄，請使用其他資料夾區分
    MEDIA_DIR="" # 不要設定為專案跟目錄，請使用其他資料夾區分
   
    # 正式環境
    # DEBUG="False"
    # SECRET_KEY=""
    # POSTGRES_PASSWORD=""
    ```
2. Docker Compose 啟動：

    在專案根目錄下執行以下命令來啟動服務：

    ```bash
    docker-compose up --build
    ```

3. 資料庫初始化：

    在容器啟動後，執行以下命令來初始化資料庫：

    ```bash
    docker exec -it traveldiary-django /bin/bash
    python manage.py migrate
    ```

4. Google OAuth 設定：
    
    ```bash
    docker exec -it traveldiary-django /bin/bash
    python manage.py setup_google_oauth
    ```

5. 建立 superuser：

    在容器中執行以下命令來建立管理員帳號：

    ```bash
    docker exec -it traveldiary-django /bin/bash
    python manage.py createsuperuser
    ```

## 開發環境設定

1. 請確保已安裝 Docker、Docker Compose、Python 3.10 以上版本、Poetry 等工具。
2. 在專案根目錄下執行以下命令來安裝依賴：

    ```bash
    poetry install
    ```
3. 參考上方部署方式中的環境變數設定，建立 `.env` 檔案。
4. 在編輯器當中的終端機，參考上方 Docker Compose 啟動方式啟動服務。
5. 日常開發中，若有修改 Python 檔案，容器中的程式會自動重啟。
   
備註：
- 開發環境中請務必使用 `DEBUG=True`，以便於除錯和開發。
- 若需要查閱錯誤訊息，請查看 Docker 容器的日誌：

    ```bash
    docker logs -f traveldiary-django
    ```
- 若有新增套件或修改 `pyproject.toml`，請執行以下命令更新 Docker 映像檔：

    ```bash
    poetry add <package_name> # 新增套件
    docker-compose up -d --build
    ```
- 若有需要對資料庫進行異動，請在程式碼修改後，執行以下命令來產生新的遷移檔，不需進入容器中：

    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

## 注意事項

1. **生產環境部署**時，請確保：
   - 設定強度足夠的 `SECRET_KEY`
   - 將 `DEBUG` 設為 `False`
   - 使用安全的資料庫密碼

2. **Nginx 設定**中的 `server_name` 需要根據實際域名進行調整

3. **媒體檔案**會儲存在 `MEDIA_DIR` 指定的路徑，請確保該路徑有適當的讀寫權限

4. **資料庫備份**：定期備份 `POSTGRES_VOLUME` 路徑下的資料

5. **登入方式**：雖然登入頁面中有提供帳號及密碼，但原則上此帳號密碼僅適用於開發環境，正式環境請使用 Google OAuth 登入。

## 聯絡資訊

作者：Nick Chen  
Email：nickchen1998@gmail.com