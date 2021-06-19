from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssetViewSet, DailyPriceViewSet

router = DefaultRouter()
router.register(r'price$', DailyPriceViewSet)
router.register(r'^$', AssetViewSet)


urlpatterns = [
    path('', include(router.urls)),
]
