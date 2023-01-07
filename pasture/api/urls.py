from django.urls import path, include


urlpatterns = [path("v1/", include("pasture.api.versioned.v1.urls"))]
