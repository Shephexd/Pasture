import os

from django.conf import settings
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

if settings.DEBUG:
    urlpatterns += [
        path("schema/", SpectacularAPIView.as_view(), name="schema"),
        path(
            "swagger/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
        path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    ]

api_path = os.path.join(settings.BASE_DIR, "api/versioned/v1/")
for _file in os.listdir(api_path):
    _url_file_path = os.path.join(api_path, _file, "urls.py")

    if os.path.exists(_url_file_path):
        urlpatterns.append(
            path(f"{_file}/", include(f"pasture.api.versioned.v1.{_file}.urls"))
        )
