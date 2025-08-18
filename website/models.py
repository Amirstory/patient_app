from django.db import models
from django.utils import timezone
from datetime import datetime



class Patient(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100, blank=True, null=True)  # Optionnel
    age = models.IntegerField(blank=True, null=True)  # Optionnel maintenant
    telephone = models.CharField(max_length=20, blank=True, null=True)  # Optionnel maintenant
    email = models.EmailField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} {self.prenom or ''}".strip()
    

class Consultation(models.Model):
    TYPE_CONSULTATION = [
        ('consultation', 'consultation'),
        ('psychoterapie', 'psychoterapie'),
        ('controle', 'controle'),
        
    ]

    STATUT_CONSULTATION = [
        ('planifie', 'planifie'),
        ('en_cours', 'en_cours'),
        ('termine', 'termine'),
        ('rapporte', 'rapporte'),
        ('annule', 'annule'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="consultations")
    type = models.CharField(max_length=50, choices=TYPE_CONSULTATION)
    date_consultation = models.DateTimeField(default=timezone.now)
    diagnostic = models.TextField(blank=True, null=True)
    traitement = models.TextField(blank=True, null=True)
    notes_medecin = models.TextField(blank=True, null=True)
    prix = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    statut = models.CharField(max_length=20, choices=STATUT_CONSULTATION, default='planifie')


    class Meta:
        ordering = ['-date_consultation']

    def __str__(self):
        return f"{self.patient} "