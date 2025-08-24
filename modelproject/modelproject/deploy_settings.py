import pymysql

from .settings_base import *
from decouple import config

pymysql.install_as_MySQLdb()

DEBUG = False

# 배포 서버의 IP 주소 및 도메인
ALLOWED_HOSTS = ["127.0.0.1", "13.124.195.3", "hufs-likelion.store"]

INTERNAL_IPS = [
    "127.0.0.1",
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# CSRF 신뢰 도메인(https 필수)
CSRF_TRUSTED_ORIGINS: list[str] = [
    "https://hufs-likelion.store",
]

CORS_ALLOWED_ORIGINS = [
    "https://hufs-likelion.store",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://localhost:3000",
    "https://127.0.0.1:3000",
    "https://localhost:5173",
    "https://127.0.0.1:5173",
]

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True  # 모든 HTTP 요청을 HTTPS로 강제

# MySQL 데이터베이스 설정
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": config("DB_NAME"),  # DB(스키마) 이름
        "USER": config("DB_USER"),  # 유저 이름 (root)
        "PASSWORD": config("DB_PASSWORD"),  # DB 비밀번호
        "HOST": config("DB_HOST"),  # DB 엔드포인트
        "PORT": 3306,
        # MYSQL Strict Mode 포함
        "OPTIONS": { 
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            "charset": "utf8mb4",
            "use_unicode": True,
        },
    }
}

AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME      = config("AWS_S3_REGION_NAME")
AWS_ACCESS_KEY_ID       = config("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY   = config("AWS_SECRET_ACCESS_KEY")

# S3 공통
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_S3_FILE_OVERWRITE = False          # 같은 이름으로 덮어쓰기 방지(특히 media)
AWS_DEFAULT_ACL = None                 # 기본 ACL 끄기(권장)
AWS_QUERYSTRING_AUTH = True            # media는 presigned URL
AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}

# URL 구성
AWS_S3_CUSTOM_DOMAIN = None  # CloudFront 쓰면 여기에 도메인

STATIC_LOCATION = config("STATIC_LOCATION", "static-dev")

# Django 4.2+ : STORAGES 방식
STORAGES = {
    # 업로드 미디어(비공개) → presigned URL 로 접근
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": AWS_STORAGE_BUCKET_NAME,
            "region_name": AWS_S3_REGION_NAME,
            "location": "media",
            "custom_domain": AWS_S3_CUSTOM_DOMAIN,
        },
    },
    # 정적 파일(공개 읽기) → collectstatic 시 S3로 업로드
    "staticfiles": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": AWS_STORAGE_BUCKET_NAME,
            "region_name": AWS_S3_REGION_NAME,
            "location": STATIC_LOCATION,
            "custom_domain": AWS_S3_CUSTOM_DOMAIN,
            "querystring_auth": False,
        },
    },
}

# (선택) 정적/미디어 URL
# 공개 static: 아래처럼 고정 URL로 접근(버킷을 퍼블릭 읽기로 설정했을 때)
STATIC_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/{STATIC_LOCATION}/"
# 비공개 media는 presigned URL 이므로 MEDIA_URL 설정은 보통 생략(필요시만 지정)
