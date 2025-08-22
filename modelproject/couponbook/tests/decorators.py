# 테스트 로그 출력용 데코레이터
def print_success_message_decorator(test_description: str):
    """
    테스트 성공 시 테스트 내용과 함께 성공 메시지를 출력하는 데코레이터입니다.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)
            print(f"테스트 성공! <테스트 내용: {test_description}>")

        return wrapper
    return decorator