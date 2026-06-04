from django.db import models
from ouvriers.models import Ouvrier
import uuid


class Pointage(models.Model):

    class Statut(models.TextChoices):
        PRESENT = 'PRESENT', 'Présent'
        ABSENT = 'ABSENT', 'Absent'
        DEMI_JOURNEE = 'DEMI', 'Demi-journée'
        CONGE = 'CONGE', 'Congé'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ouvrier = models.ForeignKey(Ouvrier, on_delete=models.CASCADE, related_name='pointages')
    date = models.DateField()
    statut = models.CharField(max_length=10, choices=Statut.choices, default=Statut.PRESENT)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['ouvrier', 'date']  # un seul pointage par ouvrier par jour

    def __str__(self):
        return f"{self.ouvrier} — {self.date} — {self.statut}"

    @property
    def coefficient(self):
        """Retourne le coefficient de calcul selon le statut"""
        coefficients = {
            'PRESENT': 1.0,
            'DEMI': 0.5,
            'ABSENT': 0.0,
            'CONGE': 0.0,
        }
        return coefficients.get(self.statut, 0.0)

    @property
    def montant_jour(self):
        """Calcule le montant pour ce jour"""
        return float(self.ouvrier.prix_journee) * self.coefficient