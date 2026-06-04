from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from django.db import transaction
from datetime import date

from .models import Pointage
from .serializers import PointageSerializer, PointageJourSerializer
from ouvriers.models import Ouvrier


class PointageListCreateView(generics.ListCreateAPIView):
    serializer_class = PointageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['ouvrier', 'statut', 'date']
    ordering_fields = ['date', 'created_at']

    def get_queryset(self):
        queryset = Pointage.objects.select_related('ouvrier').all()

        # Filtre par mois et année
        mois = self.request.query_params.get('mois')
        annee = self.request.query_params.get('annee')
        if mois:
            queryset = queryset.filter(date__month=mois)
        if annee:
            queryset = queryset.filter(date__year=annee)

        return queryset


class PointageDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PointageSerializer
    permission_classes = [IsAuthenticated]
    queryset = Pointage.objects.select_related('ouvrier').all()

    def destroy(self, request, *args, **kwargs):
        pointage = self.get_object()
        pointage.delete()
        return Response(
            {"message": "Pointage supprimé avec succès."},
            status=status.HTTP_200_OK
        )


class PointageJourView(APIView):
    """Pointer tous les ouvriers pour une date donnée en une seule requête"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PointageJourSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        date_pointage = serializer.validated_data['date']
        pointages_data = serializer.validated_data['pointages']

        resultats = []
        erreurs = []

        with transaction.atomic():
            for p in pointages_data:
                try:
                    ouvrier = Ouvrier.objects.get(id=p['ouvrier_id'])
                    pointage, created = Pointage.objects.update_or_create(
                        ouvrier=ouvrier,
                        date=date_pointage,
                        defaults={
                            'statut': p['statut'],
                            'note': p.get('note', '')
                        }
                    )
                    resultats.append({
                        'ouvrier': f"{ouvrier.nom} {ouvrier.prenom}",
                        'statut': pointage.statut,
                        'action': 'créé' if created else 'mis à jour'
                    })
                except Ouvrier.DoesNotExist:
                    erreurs.append(f"Ouvrier {p['ouvrier_id']} introuvable.")

        return Response({
            "date": date_pointage,
            "resultats": resultats,
            "erreurs": erreurs
        }, status=201)

    def get(self, request):
        """Consulter le pointage d'un jour spécifique"""
        date_param = request.query_params.get('date', str(date.today()))

        try:
            date_pointage = date.fromisoformat(date_param)
        except ValueError:
            return Response({"error": "Format de date invalide. Utilisez YYYY-MM-DD."}, status=400)

        # Tous les ouvriers actifs
        ouvriers = Ouvrier.objects.filter(statut='ACTIF')
        pointages = Pointage.objects.filter(date=date_pointage).select_related('ouvrier')
        pointages_dict = {str(p.ouvrier.id): p for p in pointages}

        resultat = []
        for ouvrier in ouvriers:
            p = pointages_dict.get(str(ouvrier.id))
            resultat.append({
                'ouvrier_id': str(ouvrier.id),
                'nom': ouvrier.nom,
                'prenom': ouvrier.prenom,
                'metier': ouvrier.metier,
                'prix_journee': float(ouvrier.prix_journee),
                'pointage_id': str(p.id) if p else None,
                'statut': p.statut if p else None,
                'statut_display': p.get_statut_display() if p else 'Non pointé',
                'montant_jour': p.montant_jour if p else 0,
                'note': p.note if p else '',
                'pointe': p is not None,
            })

        stats = {
            'total_ouvriers': len(resultat),
            'presents': sum(1 for r in resultat if r['statut'] == 'PRESENT'),
            'absents': sum(1 for r in resultat if r['statut'] == 'ABSENT'),
            'demi_journees': sum(1 for r in resultat if r['statut'] == 'DEMI'),
            'conges': sum(1 for r in resultat if r['statut'] == 'CONGE'),
            'non_pointes': sum(1 for r in resultat if not r['pointe']),
            'total_jour': sum(r['montant_jour'] for r in resultat),
        }

        return Response({
            "date": date_pointage,
            "stats": stats,
            "ouvriers": resultat
        })


class CalendrierOuvrierView(APIView):
    """Calendrier personnel d'un ouvrier"""
    permission_classes = [IsAuthenticated]

    def get(self, request, ouvrier_id):
        mois = request.query_params.get('mois', date.today().month)
        annee = request.query_params.get('annee', date.today().year)

        try:
            ouvrier = Ouvrier.objects.get(id=ouvrier_id)
        except Ouvrier.DoesNotExist:
            return Response({"error": "Ouvrier introuvable."}, status=404)

        pointages = Pointage.objects.filter(
            ouvrier=ouvrier,
            date__month=mois,
            date__year=annee
        ).order_by('date')

        calendrier = []
        for p in pointages:
            calendrier.append({
                'date': p.date,
                'statut': p.statut,
                'statut_display': p.get_statut_display(),
                'montant_jour': p.montant_jour,
                'note': p.note,
            })

        # Résumé du mois
        jours_presents = pointages.filter(statut='PRESENT').count()
        demi_journees = pointages.filter(statut='DEMI').count()
        absents = pointages.filter(statut='ABSENT').count()
        conges = pointages.filter(statut='CONGE').count()
        total_jours_payes = jours_presents + (demi_journees * 0.5)
        montant_total = total_jours_payes * float(ouvrier.prix_journee)

        return Response({
            "ouvrier": {
                "id": str(ouvrier.id),
                "nom": ouvrier.nom,
                "prenom": ouvrier.prenom,
                "prix_journee": float(ouvrier.prix_journee),
            },
            "mois": mois,
            "annee": annee,
            "resume": {
                "jours_presents": jours_presents,
                "demi_journees": demi_journees,
                "absents": absents,
                "conges": conges,
                "total_jours_payes": total_jours_payes,
                "montant_total": montant_total,
            },
            "calendrier": calendrier
        })


class ResumeMensuelView(APIView):
    """Résumé mensuel de tous les ouvriers"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        mois = int(request.query_params.get('mois', date.today().month))
        annee = int(request.query_params.get('annee', date.today().year))

        ouvriers = Ouvrier.objects.filter(statut='ACTIF')
        resultats = []

        for ouvrier in ouvriers:
            pointages = Pointage.objects.filter(
                ouvrier=ouvrier,
                date__month=mois,
                date__year=annee
            )
            jours_presents = pointages.filter(statut='PRESENT').count()
            demi_journees = pointages.filter(statut='DEMI').count()
            absents = pointages.filter(statut='ABSENT').count()
            conges = pointages.filter(statut='CONGE').count()
            total_jours_payes = jours_presents + (demi_journees * 0.5)
            montant_total = total_jours_payes * float(ouvrier.prix_journee)

            resultats.append({
                "ouvrier_id": str(ouvrier.id),
                "nom": ouvrier.nom,
                "prenom": ouvrier.prenom,
                "metier": ouvrier.metier,
                "prix_journee": float(ouvrier.prix_journee),
                "jours_presents": jours_presents,
                "demi_journees": demi_journees,
                "absents": absents,
                "conges": conges,
                "total_jours_payes": total_jours_payes,
                "montant_total": montant_total,
            })

        total_global = sum(r['montant_total'] for r in resultats)

        return Response({
            "mois": mois,
            "annee": annee,
            "total_global": total_global,
            "ouvriers": resultats
        })