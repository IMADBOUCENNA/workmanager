from django.urls import path
from .views import (
    PointageListCreateView,
    PointageDetailView,
    PointageJourView,
    CalendrierOuvrierView,
    ResumeMensuelView,
)

urlpatterns = [
    path('', PointageListCreateView.as_view()),
    path('<uuid:pk>/', PointageDetailView.as_view()),
    path('jour/', PointageJourView.as_view()),
    path('calendrier/<uuid:ouvrier_id>/', CalendrierOuvrierView.as_view()),
    path('resume-mensuel/', ResumeMensuelView.as_view()),
]