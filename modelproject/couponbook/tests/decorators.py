# 테스트 로그 출력용 데코레이터
def print_success_message(test_description: str):
    """
    테스트 성공 시 테스트 내용과 함께 성공 메시지를 출력하는 데코레이터입니다.
    """

    def decorator(func):
        def wrapper(testcase_instance):
            func(testcase_instance)
            print(f"테스트 성공! <테스트 내용: {test_description}>")

        return wrapper
    return decorator
