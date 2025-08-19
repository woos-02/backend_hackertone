from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """
    Django 애플리케이션의 설정 클래스입니다.
    앱이 로드될 때 accounts/signals.py 파일을 import하여,
    시그널 핸들러가 올바르게 등록되도록 합니다.

    이를 통해 다른 Django 앱과 분리된 상태로 이벤트에 반응하는
    로직(예: 사용자가 생성될 때 프로필 자동 생성)을 관리할 수 있습니다.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # 시그널 핸들러를 등록 
        from . import signals