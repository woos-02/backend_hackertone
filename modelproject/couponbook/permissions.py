from rest_framework.permissions import BasePermission
from rest_framework.request import Request

class IsAuthenticatedAndOwner(BasePermission):
    """
    로그인되어 있는 것은 물론, 해당 유저가 소유하고 있는 인스턴스이어야 합니다.
    """
    def has_object_permission(self, request: Request, view, obj) -> bool:
        return obj.user == request.user