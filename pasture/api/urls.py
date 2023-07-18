from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView

urlpatterns = [
    path("v1/", include("pasture.api.versioned.v1.urls")),
    path("graphql", csrf_exempt(GraphQLView.as_view(graphiql=True))),
]
