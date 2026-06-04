from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Ouvrier
from .serializers import OuvrierSerializer


class OuvrierListCreateView(generics.ListCreateAPIView):
    serializer_class = OuvrierSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['statut', 'metier']
    search_fields = ['nom', 'prenom', 'metier']
    ordering_fields = ['nom', 'prix_journee', 'created_at']

    def get_queryset(self):
        return Ouvrier.objects.all()


class OuvrierDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OuvrierSerializer
    permission_classes = [IsAuthenticated]
    queryset = Ouvrier.objects.all()

    def destroy(self, request, *args, **kwargs):
        ouvrier = self.get_object()
        ouvrier.delete()
        return Response(
            {"message": f"Ouvrier {ouvrier.nom} {ouvrier.prenom} supprimé avec succès."},
            status=status.HTTP_200_OK
        )


class OuvrierStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        total = Ouvrier.objects.count()
        actifs = Ouvrier.objects.filter(statut='ACTIF').count()
        inactifs = Ouvrier.objects.filter(statut='INACTIF').count()

        return Response({
            "total": total,
            "actifs": actifs,
            "inactifs": inactifs,
        })