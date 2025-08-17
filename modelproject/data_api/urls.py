from django.urls import path
from . import views as data_views

urlpatterns = [
    path('locations/', data_views.get_location_data, name='get_location_data'),
]