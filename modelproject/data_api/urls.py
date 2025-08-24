# from django.urls import path
# from . import views as data_views

# urlpatterns = [
#     path('locations/', data_views.get_location_data, name='get_location_data'),
#     # 계층형 원본
#     path("locations/hierarchy/", data_views.get_location_hierarchy, name="get_location_hierarchy"),
# ]

from django.urls import path
from .views import LocationListAPIView # , upload_image

urlpatterns = [
    path("locations/", LocationListAPIView.as_view(), name="get_location_data"),
    # path("upload/", upload_image, name="upload_image"),
]
