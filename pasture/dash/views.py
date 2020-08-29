from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView


class DashIndexView(TemplateView):
    template_name = 'dash/index.html'
