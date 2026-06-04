from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from datetime import date
from django.db.models import Sum

from ouvriers.models import Ouvrier
from pointages.models import Pointage
from paiements.models import Paiement
from paiements.views import calculer_salaire_mensuel
from .utils import generer_pdf_ouvrier, generer_pdf_global, generer_excel_global


class RapportPDFOuvrierView(APIView):
    """Rapport PDF mensuel d'un ouvrier"""
    permission_classes = [IsAuthenticated]

    def get(self, request, ouvrier_id):
        mois = int(request.query_params.get('mois', date.today().month))
        annee = int(request.query_params.get('annee', date.today().year))

        try:
            ouvrier = Ouvrier.objects.get(id=ouvrier_id)
        except Ouvrier.DoesNotExist:
            from rest_framework.response import Response
            return Response({"error": "Ouvrier introuvable."}, status=404)

        salaire = calculer_salaire_mensuel(ouvrier, mois, annee)
        paiements = Paiement.objects.filter(
            ouvrier=ouvrier, mois=mois, annee=annee)

        buffer = generer_pdf_ouvrier(ouvrier, salaire, paiements, mois, annee)

        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="rapport_{ouvrier.nom}_{mois}_{annee}.pdf"'
        )
        return response


class RapportPDFGlobalView(APIView):
    """Rapport PDF global tous les ouvriers"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        mois = int(request.query_params.get('mois', date.today().month))
        annee = int(request.query_params.get('annee', date.today().year))

        ouvriers = Ouvrier.objects.filter(statut='ACTIF')
        ouvriers_data = []

        for ouvrier in ouvriers:
            salaire = calculer_salaire_mensuel(ouvrier, mois, annee)
            total_paye = Paiement.objects.filter(
                ouvrier=ouvrier, mois=mois, annee=annee
            ).aggregate(total=Sum('montant'))['total'] or 0

            ouvriers_data.append({
                'nom': ouvrier.nom,
                'prenom': ouvrier.prenom,
                'metier': ouvrier.get_metier_display(),
                'prix_journee': float(ouvrier.prix_journee),
                'jours_presents': salaire['jours_presents'],
                'demi_journees': salaire['demi_journees'],
                'absents': salaire['absents'],
                'total_jours_payes': salaire['total_jours_payes'],
                'montant_du': salaire['montant_du'],
                'total_paye': float(total_paye),
                'reste_a_payer': salaire['montant_du'] - float(total_paye),
            })

        buffer = generer_pdf_global(ouvriers_data, mois, annee)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="rapport_global_{mois}_{annee}.pdf"'
        )
        return response


class RapportExcelGlobalView(APIView):
    """Export Excel global tous les ouvriers"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        mois = int(request.query_params.get('mois', date.today().month))
        annee = int(request.query_params.get('annee', date.today().year))

        ouvriers = Ouvrier.objects.filter(statut='ACTIF')
        ouvriers_data = []

        for ouvrier in ouvriers:
            salaire = calculer_salaire_mensuel(ouvrier, mois, annee)
            total_paye = Paiement.objects.filter(
                ouvrier=ouvrier, mois=mois, annee=annee
            ).aggregate(total=Sum('montant'))['total'] or 0

            ouvriers_data.append({
                'nom': ouvrier.nom,
                'prenom': ouvrier.prenom,
                'metier': ouvrier.get_metier_display(),
                'prix_journee': float(ouvrier.prix_journee),
                'jours_presents': salaire['jours_presents'],
                'demi_journees': salaire['demi_journees'],
                'absents': salaire['absents'],
                'total_jours_payes': salaire['total_jours_payes'],
                'montant_du': salaire['montant_du'],
                'total_paye': float(total_paye),
                'reste_a_payer': salaire['montant_du'] - float(total_paye),
            })

        buffer = generer_excel_global(ouvriers_data, mois, annee)
        response = HttpResponse(
            buffer,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = (
            f'attachment; filename="rapport_global_{mois}_{annee}.xlsx"'
        )
        return response