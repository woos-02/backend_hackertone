from datetime import datetime
from json import dumps, loads

from accounts.models import User
from couponbook.models import *
from decouple import config
from google import genai
from google.genai import types
from pydantic import BaseModel

from .example import get_example_statistics


class UserStatistics:
    """
    유저의 쿠폰북 이용 통계 클래스입니다. AI의 큐레이션 기능에 활용됩니다.
    """
    def __init__(self, user: User, time_format="%Y-%m-%d %H:%M"):
        """
        유저 인스턴스와 시간 포맷팅 문자열을 인자로 받습니다. 유저 인스턴스는 필수이며, 시간 포맷팅 문자열은 전달하지 않으면 기본값으로 설정됩니다.
        
        시간 포맷팅 기본값: `%Y-%m-%d %H:%M` (4자리 연도-월-일 시:분)
        """
        self.user: User = user
        self.time_format: str = time_format

    @property
    def own_couponbook(self):
        """
        해당 유저의 쿠폰북을 가져옵니다.
        """
        try:
            couponbook = CouponBook.objects.get(user=self.user)
            return couponbook
        except CouponBook.DoesNotExist:
            print("유저의 쿠폰북이 존재하지 않습니다.")

    def format_time(self, time: datetime) -> str:
        """
        datetime 인스턴스를 받아 해당 인스턴스의 시간 정보를 통계 객체의 시간 포맷팅에 맞게 포맷팅한 문자열로 반환합니다.
        """
        time_format = self.time_format
        return time.strftime(time_format)
            
    
    def extract_place_info(self, place: Place) -> dict[str, str]:
        """
        가게 인스턴스를 받아서, 가게의 정보를 딕셔너리 안에 넣어서 반환합니다.
        """
        place_info = {}
        place_info['name'] = place.name
        place_info['address'] = place.address
        return place_info
    
    def calc_current_stamps(self, coupon: Coupon) -> int:
        """
        현재까지 적립된 스탬프 수를 계산합니다.
        """
        stamps = coupon.stamps
        return stamps.count()
    
    def calc_max_stamps(self, coupon_template: CouponTemplate) -> int:
        """
        쿠폰 완성을 위해 스탬프가 몇개 필요한지를 계산합니다.
        """
        reward_info: RewardsInfo = coupon_template.reward_info
        return reward_info.amount
    
    def make_stamp_history(self, coupon: Coupon) -> list[dict]:
        """
        해당 쿠폰의 스탬프 적립 히스토리를 만듭니다.
        """
        stamps = coupon.stamps.order_by('created_at')
        history_list = []
        for number, stamp in enumerate(stamps, start=1):
            stamp_data = {}
            stamp_data['count'] = number
            stamp_data['created_at'] = self.format_time(stamp.created_at)
            history_list.append(stamp_data)
        return history_list
    
    def make_coupon_data(self, coupon: Coupon) -> dict:
        """
        쿠폰의 데이터를 만들어 딕셔너리로 반환합니다.
        """
        data = {}
        original_template = coupon.original_template
        data['place_info'] = self.extract_place_info(original_template.place)
        data['max_stamps'] = self.calc_max_stamps(original_template)
        data['current_stamps'] = self.calc_current_stamps(coupon)
        data['stamp_history'] = self.make_stamp_history(coupon)
        return data
    
    def make_history(self) -> list[dict]:
        """
        현재 보유하고 있는 쿠폰과, 쿠폰에 연결된 가게, 스탬프 적립 기록을 만들어 반환합니다.
        """
        coupons = Coupon.objects.filter(couponbook=self.own_couponbook)
        history = []
        for coupon in coupons:
            coupon_dict = {}
            coupon_dict['id'] = coupon.id
            coupon_dict['data'] = self.make_coupon_data(coupon)
            history.append(coupon_dict)
        return history

class ResponseStructure(BaseModel):
    id: int

class AICurator:
    """
    제미나이를 이용하여 쿠폰 큐레이션 기능을 제공하는 큐레이터 객체입니다.
    """
    def __init__(self, gemini_api_key: str=''):
        """
        제미나이 API 키를 인자로 받습니다. 입력하지 않거나, 빈 문자열이면 .env의 GEMINI_API_KEY 값을 사용합니다.
        """
        self.api_key = gemini_api_key or config('GEMINI_API_KEY')

    def initialize_client(self):
        """
        클라이언트 인스턴스를 생성합니다.
        """
        api_key = self.api_key
        self.client = genai.Client(api_key=api_key)

    def generate_example(self, input_data, output_data=""):
        """
        입력 데이터와 출력 데이터를 받아 예시 컨텐츠를 생성합니다. 출력 데이터는 선택적 인자이며, 전달하지 않으면 빈 문자열로 지정됩니다. (예시가 아닌 경우 활용)
        """
        PROMPT_STRING: str = """입력:
        {0}
        출력: {1}"""
        return PROMPT_STRING.format(input_data, output_data)
    
    def generate_curation_contents(self, statistics: UserStatistics) -> dict:
        """
        큐레이션을 위한 지시사항과 프롬프트를 생성하여 config와 contents를 딕셔너리로 반환합니다.
        """
        INSTRUCTION = "너는 지금부터 개인의 취향을 분석하고, 이를 토대로 주변의 음식점을 추천해주는 비서야."
        EXAMPLE_HISTORY: dict = get_example_statistics().make_history()
        example_history_json: str = dumps(EXAMPLE_HISTORY, ensure_ascii=False)
        EXAMPLE_PROMPT: str = self.generate_example(example_history_json, "{id: 1}")

        statistics_history_json: str = dumps(statistics.make_history(), ensure_ascii=False)
        input_prompt: str = self.generate_example(statistics_history_json)
        config = types.GenerateContentConfig(system_instruction=INSTRUCTION, response_mime_type='application/json', response_schema=ResponseStructure)
        contents = [
            types.Content(
                role='user', parts=[
                    types.Part(text="아래는 음식점을 추천해주는 예시야. 입력은 JSON 형식으로 주어지며, 1번 이상 방문 기록이 있는 음식점에 대해 음식점 정보와 방문 기록을 의미해."),
                    types.Part(text=EXAMPLE_PROMPT),
                    types.Part(text="다음 입력에 대해서, 추천하는 음식점을 place_info로 가지고 있는 쿠폰의 id를 출력해."),
                    types.Part(text=input_prompt),
                ]
            )
        ]

        return {'config': config, 'contents': contents}
    
    def generate_response(self, curation_contents):
        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            **curation_contents
        )

        return response
    
    def curate(self, statistics: UserStatistics) -> int:
        """
        쿠폰 큐레이션을 실행합니다. 큐레이션 결과로 추천하는 쿠폰의 id가 반환됩니다.
        """
        if not hasattr(self, 'client'):
            self.initialize_client()
        curation_contents = self.generate_curation_contents(statistics)
        response = self.generate_response(curation_contents)
        coupon_id = loads(response.text)['id']
        return coupon_id