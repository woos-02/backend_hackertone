from decimal import Decimal

from .models import KakaoMapAPIClient, KakaoMapPlace


def get_place_latlng(place_name: str) -> tuple([Decimal, Decimal]):
    """
    장소 이름에 해당하는 장소의 위도와 경도를 튜플로 반환합니다.
    """
    client = KakaoMapAPIClient()
    place: KakaoMapPlace | None = client.find_place_by_keyword(place_name)
    
    if place:
        return place.get_latlng()
    
    print(f"장소의 검색 결과가 없습니다. ({place_name})")