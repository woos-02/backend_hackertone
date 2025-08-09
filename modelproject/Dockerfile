# FROM python:3.10.12

# ENV PYTHONUNBUFFERED 1

# RUN apt-get -y update
# RUN apt-get -y install vim

# RUN mkdir /app
# ADD . /app
# WORKDIR /app
# COPY .python-version .

# RUN pip install --upgrade pip
# RUN pip install -r requirements.txt
# COPY .env .

# COPY requirements-prod.txt .
# RUN pip install --no-cache-dir -r requirements-prod.txt

# ---- base ----

FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # uv가 만든 .venv를 기본 PATH에 등록
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# 시스템 패키지
# - build-essential/gcc: C 확장 빌드
# - pkg-config: mysqlclient 빌드 시 라이브러리/헤더 탐색 (필수!)
# - default-libmysqlclient-dev: MySQL/MariaDB 클라이언트 개발 헤더
#   (MariaDB를 직접 쓰면 libmariadb-dev로 교체 가능)
# - curl/ca-certificates: 일반 유틸
# - vim: 선택(편의)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc pkg-config default-libmysqlclient-dev \
    curl ca-certificates vim \
 && rm -rf /var/lib/apt/lists/*

# uv 설치
RUN python -m pip install --upgrade pip && pip install uv

# 의존성만 먼저 복사 → 레이어 캐시 극대화 (uv는 pyproject.toml/uv.lock 사용)
COPY pyproject.toml uv.lock* ./

# 프로덕션 의존성만 동기화(가상환경 .venv 생성)
# --frozen: uv.lock과 불일치 시 실패 → 재현 가능한 빌드
RUN uv sync --no-dev --extra prod --frozen

# 앱 소스 복사
COPY . .

# ⚠️ .env는 이미지에 포함하지 않는 것을 권장 (런타임에 --env-file 등으로 주입)
# COPY .env .

# 개발 서버 예시 (실서비스는 gunicorn/uwsgi 권장)
# CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]

# 예: gunicorn으로 실행 (원하시면 주석 해제)
# CMD ["uv", "run", "gunicorn", "modelproject.wsgi:application", "-b", "0.0.0.0:8000"]
