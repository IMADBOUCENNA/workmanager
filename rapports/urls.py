from django.urls import path
from .views import (
    RapportPDFOuvrierView,
    RapportPDFGlobalView,
    RapportExcelGlobalView,
)

urlpatterns = [
    path('pdf/ouvrier/<uuid:ouvrier_id>/', RapportPDFOuvrierView.as_view()),
    path('pdf/global/', RapportPDFGlobalView.as_view()),
    path('excel/global/', RapportExcelGlobalView.as_view()),
]