from django.urls import path
from .views import (
    PaiementListCreateView,
    PaiementDetailView,
    SalaireOuvrierView,
    SalaireGlobalView,
    DashboardView,
)

urlpatterns = [
    path('', PaiementListCreateView.as_view()),
    path('<uuid:pk>/', PaiementDetailView.as_view()),
    path('salaire/<uuid:ouvrier_id>/', SalaireOuvrierView.as_view()),
    path('salaire-global/', SalaireGlobalView.as_view()),
    path('dashboard/', DashboardView.as_view()),
]