from django.urls import path

from .views import DashIndexView

urlpatterns = [path(r"", DashIndexView.as_view())]
