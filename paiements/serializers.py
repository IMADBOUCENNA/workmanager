from rest_framework import serializers
from .models import Paiement
from ouvriers.serializers import OuvrierSerializer


class PaiementSerializer(serializers.ModelSerializer):
    ouvrier_detail = OuvrierSerializer(source='ouvrier', read_only=True)

    class Meta:
        model = Paiement
        fields = [
            'id', 'ouvrier', 'ouvrier_detail', 'montant',
            'date_paiement', 'mois', 'annee', 'note', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def validate_montant(self, value):
        if value <= 0:
            raise serializers.ValidationError("Le montant doit être supérieur à 0.")
        return value