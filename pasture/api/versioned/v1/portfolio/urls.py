from rest_framework.routers import DefaultRouter
from .views import PortfolioViewSet

router = DefaultRouter()
router.register(r'', PortfolioViewSet)


urlpatterns = router.urls + [
]
