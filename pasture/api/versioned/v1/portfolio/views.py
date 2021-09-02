import logging
from rest_framework import viewsets
from pasture.portfolio.models import Portfolio
from .serializers import PortfolioSerializer

logger = logging.getLogger('pasture')


class PortfolioViewSet(viewsets.ModelViewSet):
    serializer_class = PortfolioSerializer
    queryset = Portfolio.objects.all()
