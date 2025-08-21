"""
데이터 API 뷰.

이 모듈은 위치 데이터를 처리하고 반환하는 Django 뷰를 포함합니다.
주요 기능은 JSON 파일에서 위치 데이터를 읽어와 HTTP 응답으로 제공하는 것입니다.
"""
from pathlib import Path
from typing import List, Dict, Any
from django.conf import settings
from django.http import JsonResponse, HttpRequest
import json

CANDIDATES = [
    Path(settings.BASE_DIR) / "data" / "locations.json",                  # 루트/data 우선
    Path(settings.BASE_DIR) / "modelproject" / "data" / "locations.json", # 기존 경로도 시도
]

def _find_locations_json() -> Path:
    for p in CANDIDATES:
        if p.exists():
            return p
    return CANDIDATES[0]

def _flatten(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    locations.json을 '시/구/동/코드'의 평탄화 리스트로 변환합니다.
    새 포맷(payload["index"])과 구 포맷(트리/문자열리스트) 모두 대응.
    """
    if isinstance(payload, dict) and "index" in payload:
        # 새 포맷: 이미 평탄화된 index를 그대로 사용
        return [
            {
                "province": it.get("province"),
                "city": it.get("city"),
                "district": it.get("district"),
                "code": it.get("code"),
            }
            for it in payload["index"]
        ]

    # 구 포맷: 트리에서 평탄화
    flat: List[Dict[str, Any]] = []
    for prov, cities in payload.items():
        for city, districts in cities.items():
            for d in districts:
                if isinstance(d, dict):
                    flat.append({
                        "province": prov,
                        "city": city,
                        "district": d.get("district"),
                        "code": d.get("code"),
                    })
                else:
                    flat.append({
                        "province": prov,
                        "city": city,
                        "district": d,
                        "code": None,
                    })
    return flat

def _load_flat() -> List[Dict[str, Any]]:
    loc_file = _find_locations_json()
    with loc_file.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return _flatten(raw)

def get_location_data(request: HttpRequest):
    """
    기본: 평탄화 리스트([{province, city, district, code}, ...]) 반환

    옵션(쿼리 파라미터):
      - province=서울특별시     : 시/도 완전일치 필터
      - city=종로구             : 시/군/구 완전일치 필터
      - d=가회                  : 동 이름 부분검색
      - code=1111014600         : 법정동코드 완전일치
      - code_prefix=11110       : 법정동코드 접두 일치(예: 종로구 전체)
      - mode=string             : "서울특별시 종로구 가회동 1111014600" 문자열 리스트로 반환
    """
    try:
        flat = _load_flat()
    except FileNotFoundError:
        return JsonResponse(
            {"detail": "locations.json not found", "tried": [str(p) for p in CANDIDATES]},
            status=500
        )
    except json.JSONDecodeError:
        return JsonResponse(
            {"detail": "locations.json is not valid JSON"},
            status=500
        )

    # 필터
    province = request.GET.get("province")
    city = request.GET.get("city")
    d = request.GET.get("d")
    code = request.GET.get("code")
    code_prefix = request.GET.get("code_prefix")

    if province:
        flat = [r for r in flat if r["province"] == province]
    if city:
        flat = [r for r in flat if r["city"] == city]
    if d:
        flat = [r for r in flat if r["district"] and d in r["district"]]
    if code:
        flat = [r for r in flat if r["code"] == code]
    if code_prefix:
        flat = [r for r in flat if r["code"] and r["code"].startswith(code_prefix)]

    # 출력 형태 선택
    if request.GET.get("mode") == "string":
        out = [f'{r["province"]} {r["city"]} {r["district"]} {r["code"] or ""}'.strip() for r in flat]
        return JsonResponse(out, safe=False)

    return JsonResponse(flat, safe=False)

def get_location_hierarchy(request: HttpRequest):
    """
    계층형(hierarchy)만 보여주는 엔드포인트.
    프론트에서 3단 드롭다운(시/군구/동) 구성에 쓰기 좋습니다.
    """
    loc_file = _find_locations_json()
    try:
        with loc_file.open("r", encoding="utf-8") as f:
            raw = json.load(f)
    except FileNotFoundError:
        return JsonResponse(
            {"detail": "locations.json not found", "tried": [str(p) for p in CANDIDATES]},
            status=500
        )

    # 새 포맷이면 hierarchy만 꺼내고, 구 포맷이면 그대로 반환
    if isinstance(raw, dict) and "hierarchy" in raw:
        raw = raw["hierarchy"]
    return JsonResponse(raw, safe=False)
