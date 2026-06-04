from rest_framework import serializers
from .models import Ouvrier


class OuvrierSerializer(serializers.ModelSerializer):
    metier_display = serializers.CharField(source='get_metier_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)

    class Meta:
        model = Ouvrier
        fields = [
            'id', 'nom', 'prenom', 'metier', 'metier_display',
            'telephone', 'adresse', 'prix_journee',
            'statut', 'statut_display', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def validate_prix_journee(self, value):
        if value <= 0:
            raise serializers.ValidationError("Le prix de la journée doit être supérieur à 0.")
        return value

    def validate_telephone(self, value):
        if value and not value.replace('+', '').replace(' ', '').isdigit():
            raise serializers.ValidationError("Numéro de téléphone invalide.")
        return value