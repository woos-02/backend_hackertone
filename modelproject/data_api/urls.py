from django.urls import path
from . import views as data_views

urlpatterns = [
    path('locations/', data_views.get_location_data, name='get_location_data'),
    # 계층형 원본
    path("locations/hierarchy/", data_views.get_location_hierarchy, name="get_location_hierarchy"),
]