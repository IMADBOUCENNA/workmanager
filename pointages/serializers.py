from rest_framework import serializers
from .models import Pointage
from ouvriers.models import Ouvrier
from ouvriers.serializers import OuvrierSerializer


class PointageSerializer(serializers.ModelSerializer):
    ouvrier_detail = OuvrierSerializer(source='ouvrier', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    coefficient = serializers.FloatField(read_only=True)
    montant_jour = serializers.FloatField(read_only=True)

    class Meta:
        model = Pointage
        fields = [
            'id', 'ouvrier', 'ouvrier_detail', 'date',
            'statut', 'statut_display', 'note',
            'coefficient', 'montant_jour', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def validate(self, data):
        # Vérifier que l'ouvrier est actif
        ouvrier = data.get('ouvrier')
        if ouvrier and ouvrier.statut == 'INACTIF':
            raise serializers.ValidationError("Impossible de pointer un ouvrier inactif.")
        return data


class PointageJourSerializer(serializers.Serializer):
    """Pour pointer plusieurs ouvriers en une seule requête"""
    date = serializers.DateField()
    pointages = serializers.ListField(
        child=serializers.DictField()
    )

    def validate_pointages(self, value):
        statuts_valides = ['PRESENT', 'ABSENT', 'DEMI', 'CONGE']
        for p in value:
            if 'ouvrier_id' not in p:
                raise serializers.ValidationError("ouvrier_id requis pour chaque pointage.")
            if 'statut' not in p:
                raise serializers.ValidationError("statut requis pour chaque pointage.")
            if p['statut'] not in statuts_valides:
                raise serializers.ValidationError(f"Statut invalide : {p['statut']}")
        return value


class ResumeMensuelSerializer(serializers.Serializer):
    """Résumé mensuel d'un ouvrier"""
    ouvrier_id = serializers.UUIDField()
    ouvrier_nom = serializers.CharField()
    mois = serializers.IntegerField()
    annee = serializers.IntegerField()
    jours_presents = serializers.IntegerField()
    jours_absents = serializers.IntegerField()
    demi_journees = serializers.IntegerField()
    conges = serializers.IntegerField()
    total_jours_payes = serializers.FloatField()
    montant_total = serializers.FloatField()