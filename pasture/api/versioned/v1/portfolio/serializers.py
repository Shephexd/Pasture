from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer
from pasture.portfolio.models import Portfolio


class PortfolioSerializer(ModelSerializer):
    class Meta:
        model = Portfolio
        fields = ('id', 'weights')

    def validate_weights(self, weights):
        if sum([w['weight'] for w in weights]) != 1:
            raise ValidationError("sum of weights must be 1")
        return weights
