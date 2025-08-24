from decimal import Decimal

import requests
from decouple import config


class KakaoMapPlace:
    """
    카카오맵 검색 결과로 나타나는 장소 정보를 클래스화하였습니다.
    """
    def __init__(self, place_dict: dict):
        """
        장소 딕셔너리를 전달받아 해당 딕셔너리의 정보를 바탕으로 인스턴스를 초기화합니다. 
        """
        for key in place_dict:
           setattr(self, key, place_dict[key]) 
    
    def __str__(self):
        return f"KakaoMapPlace 인스턴스 > 장소명: {self.place_name}"
    
    def get_latlng(self) -> tuple[Decimal, Decimal]:
        """
        위도(y)와 경도(x)를 튜플 형태로 반환합니다.
        """
        latlng = self.y, self.x
        return tuple(map(Decimal, latlng))

class KakaoMapAPIClient:
    """
    REST API를 사용해서 카카오맵 API와 통신하는 클라이언트입니다.
    """
    def __init__(self, kakao_rest_api_key=None):
        """
        카카오 디벨로퍼스 앱의 REST API 키가 필요합니다. (확인: 앱 > 앱 설정 > 앱 > 일반)

        REST API 키를 전달하지 않으면, .env에 있는 KAKAO_REST_API_KEY 값을 찾습니다.
        """
        if not kakao_rest_api_key:
            try:
                kakao_rest_api_key = config('KAKAO_REST_API_KEY')
            except:
                raise Exception("REST API 키가 전달되지 않았습니다. 그러나 .env 파일에도 KAKAO_REST_API_KEY가 존재하지 않습니다.")
        
        self.kakao_rest_api_key = kakao_rest_api_key
    
    def generate_auth_header(self) -> dict:
        """
        카카오맵 API와 통신하기 위해 필요한 Authorization 헤더를 생성합니다. 
        """
        auth_value = f'KakaoAK {self.kakao_rest_api_key}'
        header = {'Authorization': auth_value}
        return header
    
    def find_place_by_keyword(self, keyword: str, **kwargs) -> KakaoMapPlace | None:
        """
        장소를 검색하여 제일 먼저 나타나는 장소 정보를 바탕으로 KakaoMapPlace 인스턴스를 만들어 돌려줍니다.

        검색 결과가 없으면 None이 반환됩니다.

        keyword는 필수 인자이며, 나머지는 https://developers.kakao.com/docs/latest/ko/local/dev-guide#search-by-keyword 문서의 쿼리 파라미터 값을 받습니다.
        """
        payload = {'query': keyword, **kwargs}
        header = self.generate_auth_header()
        r = requests.get('https://dapi.kakao.com/v2/local/search/keyword', params=payload, headers=header)

        documents: dict = r.json()['documents']
        if documents:
            return KakaoMapPlace(documents[0])
        
        return None