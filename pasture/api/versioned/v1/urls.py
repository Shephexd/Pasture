import os
from django.conf import settings
from django.urls import path, include


urlpatterns = [

]

api_path = os.path.join(settings.BASE_DIR, 'api/versioned/v1/')
for _file in os.listdir(api_path):
    _url_file_path = os.path.join(api_path, _file, 'urls.py')

    if os.path.exists(_url_file_path):
        urlpatterns.append(
            path(f"{_file}/", include(f"pasture.api.versioned.v1.{_file}.urls"))
        )
