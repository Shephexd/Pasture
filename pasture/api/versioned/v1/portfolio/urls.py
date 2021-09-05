from rest_framework.routers import DefaultRouter
from .views import PortfolioViewSet, HierarchicalRiskParityViewSet

router = DefaultRouter()
router.register(r'hrp', HierarchicalRiskParityViewSet)
router.register(r'', PortfolioViewSet)


urlpatterns = [
] + router.urls
