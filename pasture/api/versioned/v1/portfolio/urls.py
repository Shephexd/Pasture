from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import PortfolioViewSet

router = DefaultRouter()
router.register(r"", PortfolioViewSet)


urlpatterns = [
    path("latest", PortfolioViewSet.as_view({"get": "get_latest"})),
    path("model/", PortfolioViewSet.as_view({"post": "run_model"})),
    path("simulate/qty/", PortfolioViewSet.as_view({"post": "calc_shares"})),
] + router.urls
