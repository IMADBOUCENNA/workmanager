from django.urls import path
from .views import OuvrierListCreateView, OuvrierDetailView, OuvrierStatsView

urlpatterns = [
    path('', OuvrierListCreateView.as_view()),
    path('<uuid:pk>/', OuvrierDetailView.as_view()),
    path('stats/', OuvrierStatsView.as_view()),
]