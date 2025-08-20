from decimal import Decimal

from .models import KakaoMapAPIClient, KakaoMapPlace


def get_place_latlng(place_name: str) -> tuple([Decimal, Decimal]):
    """
    장소 이름에 해당하는 장소의 위도와 경도를 튜플로 반환합니다.
    """
    client = KakaoMapAPIClient()
    place: KakaoMapPlace = client.find_place_by_keyword(place_name)
    return place.get_latlng()