"""
데이터 API 뷰.

이 모듈은 위치 데이터를 처리하고 반환하는 Django 뷰를 포함합니다.
주요 기능은 JSON 파일에서 위치 데이터를 읽어와 HTTP 응답으로 제공하는 것입니다.
"""

from django.http import JsonResponse
import json
import os

def get_location_data(request) -> JsonResponse:
    """
    위치 데이터를 JSON 응답으로 반환합니다.

    이 함수는 'data/locations.json' 파일에서 위치 정보를 읽어와
    HTTP GET 요청에 대한 JSON 응답으로 반환하는 Django 뷰입니다.
    
    Args:
        request (HttpRequest): 클라이언트로부터의 HTTP 요청 객체.
    
    Returns:
        JsonResponse: 'data/locations.json' 파일의 내용을 담은 JSON 응답.
                      파일을 찾을 수 없거나 읽기 오류가 발생하면 빈 딕셔너리를 반환합니다.
    """
    # JSON 파일 경로 설정
    # __file__은 views.py의 경로를 나타냅니다.
    # os.path.dirname(__file__)은 views.py가 있는 디렉토리(예: data_api)를 가져옵니다.
    # '..'를 사용하여 부모 디렉토리(프로젝트 최상위)로 이동합니다.
    # 'data' 폴더와 'locations.json' 파일을 경로에 합칩니다.
    file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'locations.json')
    
    # 파일을 열어 데이터 로드
    # 'r' 모드는 읽기 모드입니다.
    # encoding='utf-8'은 한글 깨짐을 방지합니다.
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f) # 파일을 읽어 JSON 데이터를 파이썬 딕셔너리로 변환
        
    return JsonResponse(data) # 딕셔너리를 JSON 응답으로 반환