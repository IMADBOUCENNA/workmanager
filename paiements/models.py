from django.db import models
from ouvriers.models import Ouvrier
import uuid


class Paiement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ouvrier = models.ForeignKey(Ouvrier, on_delete=models.CASCADE, related_name='paiements')
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date_paiement = models.DateField()
    mois = models.IntegerField()
    annee = models.IntegerField()
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_paiement']

    def __str__(self):
        return f"{self.ouvrier} — {self.montant} DA — {self.date_paiement}"