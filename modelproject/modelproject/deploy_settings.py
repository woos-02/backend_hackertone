import pymysql

from .settings_base import *

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
