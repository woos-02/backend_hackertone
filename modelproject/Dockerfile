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

# 시스템 패키지 (mysqlclient 등을 쓸 때 컴파일 도구가 필요합니다)
# ※ DB가 PostgreSQL이면 `default-libmysqlclient-dev` 대신 `libpq-dev`로 바꾸세요.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc curl ca-certificates default-libmysqlclient-dev vim \
 && rm -rf /var/lib/apt/lists/*

# uv 설치
RUN python -m pip install --upgrade pip && pip install uv

# 의존성만 먼저 복사 → 레이어 캐시 극대화
# (uv는 pyproject.toml/uv.lock을 사용)
COPY pyproject.toml uv.lock* ./

# 프로덕션 의존성만 동기화(가상환경 .venv 생성)
# --frozen: uv.lock과 불일치 시 실패 → 재현 가능 빌드
RUN uv sync --no-dev --extra prod --frozen

# 앱 소스 복사
COPY . .

# 선택: pyenv 파일이 굳이 필요하진 않지만 유지하려면 아래 주석 해제
# COPY .python-version .

# ⚠️ .env는 이미지에 굽지 않는 것을 권장합니다(비밀 유출 위험).
# 런타임에 -e/--env-file로 주입하거나 오케스트레이션에서 관리하세요.
# COPY .env .

# 예: 장고 개발 서버 실행(실서비스는 gunicorn/uwsgi 권장)
# CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
