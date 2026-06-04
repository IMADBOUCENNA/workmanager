from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum
from datetime import date

from .models import Paiement
from .serializers import PaiementSerializer
from ouvriers.models import Ouvrier
from pointages.models import Pointage


def calculer_salaire_mensuel(ouvrier, mois, annee):
    """Calcule le salaire dû pour un ouvrier sur un mois donné"""
    pointages = Pointage.objects.filter(
        ouvrier=ouvrier,
        date__month=mois,
        date__year=annee
    )
    jours_presents = pointages.filter(statut='PRESENT').count()
    demi_journees = pointages.filter(statut='DEMI').count()
    total_jours_payes = jours_presents + (demi_journees * 0.5)
    montant_du = total_jours_payes * float(ouvrier.prix_journee)
    return {
        'jours_presents': jours_presents,
        'demi_journees': demi_journees,
        'absents': pointages.filter(statut='ABSENT').count(),
        'conges': pointages.filter(statut='CONGE').count(),
        'total_jours_payes': total_jours_payes,
        'montant_du': montant_du,
    }


class PaiementListCreateView(generics.ListCreateAPIView):
    serializer_class = PaiementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['ouvrier', 'mois', 'annee']

    def get_queryset(self):
        return Paiement.objects.select_related('ouvrier').all()


class PaiementDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PaiementSerializer
    permission_classes = [IsAuthenticated]
    queryset = Paiement.objects.select_related('ouvrier').all()

    def destroy(self, request, *args, **kwargs):
        paiement = self.get_object()
        paiement.delete()
        return Response(
            {"message": "Paiement supprimé avec succès."},
            status=status.HTTP_200_OK
        )


class SalaireOuvrierView(APIView):
    """Détail financier complet d'un ouvrier pour un mois"""
    permission_classes = [IsAuthenticated]

    def get(self, request, ouvrier_id):
        mois = int(request.query_params.get('mois', date.today().month))
        annee = int(request.query_params.get('annee', date.today().year))

        try:
            ouvrier = Ouvrier.objects.get(id=ouvrier_id)
        except Ouvrier.DoesNotExist:
            return Response({"error": "Ouvrier introuvable."}, status=404)

        # Calcul salaire
        salaire = calculer_salaire_mensuel(ouvrier, mois, annee)

        # Paiements effectués ce mois
        paiements = Paiement.objects.filter(
            ouvrier=ouvrier,
            mois=mois,
            annee=annee
        )
        total_paye = paiements.aggregate(
            total=Sum('montant'))['total'] or 0
        reste = salaire['montant_du'] - float(total_paye)

        return Response({
            "ouvrier": {
                "id": str(ouvrier.id),
                "nom": ouvrier.nom,
                "prenom": ouvrier.prenom,
                "metier": ouvrier.metier,
                "prix_journee": float(ouvrier.prix_journee),
            },
            "mois": mois,
            "annee": annee,
            "pointage": salaire,
            "financier": {
                "montant_du": salaire['montant_du'],
                "total_paye": float(total_paye),
                "reste_a_payer": reste,
            },
            "historique_paiements": PaiementSerializer(paiements, many=True).data
        })


class SalaireGlobalView(APIView):
    """Résumé financier global de tous les ouvriers pour un mois"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        mois = int(request.query_params.get('mois', date.today().month))
        annee = int(request.query_params.get('annee', date.today().year))

        ouvriers = Ouvrier.objects.filter(statut='ACTIF')
        resultats = []
        total_du_global = 0
        total_paye_global = 0

        for ouvrier in ouvriers:
            salaire = calculer_salaire_mensuel(ouvrier, mois, annee)
            total_paye = Paiement.objects.filter(
                ouvrier=ouvrier, mois=mois, annee=annee
            ).aggregate(total=Sum('montant'))['total'] or 0

            reste = salaire['montant_du'] - float(total_paye)
            total_du_global += salaire['montant_du']
            total_paye_global += float(total_paye)

            resultats.append({
                "ouvrier_id": str(ouvrier.id),
                "nom": ouvrier.nom,
                "prenom": ouvrier.prenom,
                "metier": ouvrier.metier,
                "prix_journee": float(ouvrier.prix_journee),
                "jours_presents": salaire['jours_presents'],
                "demi_journees": salaire['demi_journees'],
                "total_jours_payes": salaire['total_jours_payes'],
                "montant_du": salaire['montant_du'],
                "total_paye": float(total_paye),
                "reste_a_payer": reste,
            })

        return Response({
            "mois": mois,
            "annee": annee,
            "resume_global": {
                "total_du": total_du_global,
                "total_paye": total_paye_global,
                "reste_global": total_du_global - total_paye_global,
            },
            "ouvriers": resultats
        })


class DashboardView(APIView):
    """Tableau de bord global"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = date.today()
        mois = today.month
        annee = today.year

        # Stats ouvriers
        total_ouvriers = Ouvrier.objects.count()
        ouvriers_actifs = Ouvrier.objects.filter(statut='ACTIF').count()

        # Stats pointage aujourd'hui
        pointages_today = Pointage.objects.filter(date=today)
        presents = pointages_today.filter(statut='PRESENT').count()
        absents = pointages_today.filter(statut='ABSENT').count()
        demi = pointages_today.filter(statut='DEMI').count()
        conges = pointages_today.filter(statut='CONGE').count()

        # Stats financières du mois
        ouvriers = Ouvrier.objects.filter(statut='ACTIF')
        total_du_mois = 0
        total_paye_mois = 0

        for ouvrier in ouvriers:
            salaire = calculer_salaire_mensuel(ouvrier, mois, annee)
            total_du_mois += salaire['montant_du']
            total_paye = Paiement.objects.filter(
                ouvrier=ouvrier, mois=mois, annee=annee
            ).aggregate(total=Sum('montant'))['total'] or 0
            total_paye_mois += float(total_paye)

        return Response({
            "date": today,
            "ouvriers": {
                "total": total_ouvriers,
                "actifs": ouvriers_actifs,
                "inactifs": total_ouvriers - ouvriers_actifs,
            },
            "pointage_aujourd_hui": {
                "presents": presents,
                "absents": absents,
                "demi_journees": demi,
                "conges": conges,
                "total_pointes": pointages_today.count(),
            },
            "financier_mois": {
                "mois": mois,
                "annee": annee,
                "total_du": total_du_mois,
                "total_paye": total_paye_mois,
                "reste_global": total_du_mois - total_paye_mois,
            }
        })