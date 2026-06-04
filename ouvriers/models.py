from django.db import models
import uuid


class Ouvrier(models.Model):

    class Metier(models.TextChoices):
        MACON = 'MACON', 'Maçon'
        ELECTRICIEN = 'ELECTRICIEN', 'Électricien'
        PLOMBIER = 'PLOMBIER', 'Plombier'
        PEINTRE = 'PEINTRE', 'Peintre'
        CARRELEUR = 'CARRELEUR', 'Carreleur'
        CHARPENTIER = 'CHARPENTIER', 'Charpentier'
        SOUDEUR = 'SOUDEUR', 'Soudeur'
        MANŒUVRE = 'MANOEUVRE', 'Manœuvre'
        AUTRE = 'AUTRE', 'Autre'

    class Statut(models.TextChoices):
        ACTIF = 'ACTIF', 'Actif'
        INACTIF = 'INACTIF', 'Inactif'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    metier = models.CharField(max_length=50, choices=Metier.choices, default=Metier.AUTRE)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    prix_journee = models.DecimalField(max_digits=10, decimal_places=2)
    statut = models.CharField(max_length=10, choices=Statut.choices, default=Statut.ACTIF)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nom', 'prenom']

    def __str__(self):
        return f"{self.nom} {self.prenom} — {self.metier}"