# Production settings for Hina Travel Diary
# Import all settings from base settings
from .settings import *
import os

# Security settings for production
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']  # 請更換為您的網域

# Database configuration for production
# 您可以根據需要配置 PostgreSQL 或其他資料庫
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.environ.get('DB_NAME'),
#         'USER': os.environ.get('DB_USER'),
#         'PASSWORD': os.environ.get('DB_PASSWORD'),
#         'HOST': os.environ.get('DB_HOST'),
#         'PORT': os.environ.get('DB_PORT', '5432'),
#     }
# }

# Security settings
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'

# Use environment variable for secret key
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# WhiteNoise configuration (already configured in base settings)
# No additional configuration needed for production