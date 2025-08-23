from pathlib import Path
from typing import List, Dict, Any

from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
import json
from functools import lru_cache

"""
위치(시/도-시/군/구-읍/면/동) 데이터를 반환하는 API 뷰
- GET /api/locations/ -> 전체 트리(JSON 파일 그대로)
- GET /api/locations/?province=서울특별시 -> 해당 시/도에 속한 시/군/구 목록(문자열 배열)
- GET /api/locations/?province=서울특별시&city=종로구 -> 해당 시/군/구의 읍/면/동 목록(문자열 배열)
"""

# locations.json 경로 (create_locations.py가 저장하는 위치와 동일)
LOC_FILE = Path(settings.BASE_DIR) / "modelproject" / "data" / "locations.json"


@lru_cache(maxsize=1)
def _load_locations() -> dict:
    """
    파일을 읽어 딕셔너리로 반환합니다. (간단 캐시)
    파일이 갱신되면 서버 재시작 시 자동 반영됩니다.
    """
    try:
        with LOC_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


class LocationListAPIView(APIView):
    """
    위치 데이터 조회용 엔드포인트
    - 전체 구조: { 시도: { 시군구: [읍/면/동, ...] } }
    - 쿼리 파라미터로 부분 조회 지원
    """

    def get(self, request):
        data = _load_locations()
        if not data:
            return Response(
                {"detail": "locations.json not found or invalid", "path": str(LOC_FILE)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        province = request.query_params.get("province")
        city = request.query_params.get("city")

        # 1) province & city → 해당 시/군/구의 읍/면/동 배열
        if province and city:
            districts = data.get(province, {}).get(city, [])
            return Response(districts, status=status.HTTP_200_OK)

        # 2) province만 → 해당 시/도의 시/군/구 목록
        if province:
            cities = list(data.get(province, {}).keys())
            return Response(cities, status=status.HTTP_200_OK)

        # 3) 파라미터 없음 → 전체 트리 반환
        return Response(data, status=status.HTTP_200_OK)


from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.core.files.storage import default_storage

@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def upload_image(request):
    f = request.FILES["file"]            # form-data key: file
    path = default_storage.save(f"uploads/{f.name}", f)
    url = default_storage.url(path)      # presigned URL(만료됨)
    return Response({"path": path, "url": url})