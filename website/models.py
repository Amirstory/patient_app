# models.py
from django.db import models
from django.utils import timezone

class Patient(models.Model):
    # === INFORMATIONS DE BASE (comme avant) ===
    nom = models.CharField(max_length=100)  # Nom obligatoire
    prenom = models.CharField(max_length=100, blank=True, null=True)  # Prénom optionnel
    
    # === NOUVELLES INFORMATIONS SIMPLES ===
    # DateField = pour stocker une date (jour/mois/année)
    date_naissance = models.DateField(blank=True, null=True)  # Au lieu de l'âge
    
    # Choix simple pour le sexe
    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES, blank=True, null=True)
    
    # === COORDONNEES (comme avant) ===
    telephone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    # Adresse en un seul champ
    adresse = models.TextField(blank=True, null=True)

    
    # === INFORMATIONS SYSTEME ===
    date_creation = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True, help_text="Notes privées du praticien")
    profession = models.CharField(max_length=100, blank=True, null=True)

    
    # === METHODES ===
    def __str__(self):
        return f"{self.nom} {self.prenom or ''}".strip()
    
    @property
    def age(self):
        # Calcul automatique de l'âge
        if self.date_naissance:
            today = timezone.now().date()
            return today.year - self.date_naissance.year - (
                (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day)
            )
        return None
    

#------------------------------CONSULTATION--------------------------------------------------------------------------------
from django.db import models, transaction, IntegrityError


class Consultations(models.Model):
    """
    Modèle pour gérer les consultations des patients
    Compatible avec votre code existant + prix automatiques
    """
    
    # === VOS CHOIX EXISTANTS (gardés identiques) ===
    TYPE_CONSULTATION = [
        ('consultation', 'Consultation'),  # Prix : 400 DH
        ('controle', 'Contrôle'),         # Prix : 0 DH (gratuit)
        ('seance_psycho', 'Séance Psychotérapique'),  # Prix : 700 DH
    ]

    STATUT_CONSULTATION = [
        ('planifie', 'Planifié'),      # Petit ajustement d'affichage
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('rapporte', 'Reporté'),       # Petit ajustement d'affichage
        ('annule', 'Annulé'),
    ]
    
    # === VOS CHAMPS EXISTANTS (gardés identiques) ===
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="consultations")
    numero = models.PositiveIntegerField(editable=False, null=True, blank=True, db_index=True)  # ⬅️ NOUVEAU
    type = models.CharField(max_length=50, choices=TYPE_CONSULTATION, help_text="Le prix sera automatiquement calculé selon le type")
    date_consultation = models.DateTimeField(default=timezone.now)
    diagnostic = models.TextField(blank=True, null=True)
    prix = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    statut = models.CharField(max_length=20, choices=STATUT_CONSULTATION, default='planifie')

    # === NOUVELLES METHODES (ajoutées sans casser l'existant) ===
    def save(self, *args, **kwargs):
        """
        NOUVEAU : Calcul automatique des prix selon le type
        Cette méthode s'exécute à chaque sauvegarde
        """
        # Dictionnaire des prix selon le type
        prix_par_type = {
            'consultation': 400,      # Consultation = 400 DH
            'controle': 0,           # Contrôle = gratuit
            'seance_psycho': 700,    # Séance psycho = 700 DH
        }
        
        # Attribuer le prix automatiquement selon le type
        self.prix = prix_par_type.get(self.type, 0)
        
        # Sauvegarder normalement
        super().save(*args, **kwargs)
    
    def __str__(self):
        """
        AMELIORE : Affichage plus informatif
        """
        return f"{self.patient.nom} - {self.get_type_display()} - {self.date_consultation.strftime('%d/%m/%Y')}"
    
    @property
    def type_display_avec_prix(self):
        """
        NOUVEAU : Affiche le type avec le prix
        Utile pour les templates
        """
        prix_text = f" ({self.prix} DH)" if self.prix > 0 else " (Gratuit)"
        return f"{self.get_type_display()}{prix_text}"

    class Meta:
        """
        Configuration du modèle (gardée identique + ajouts)
        """
        ordering = ['-date_consultation']
        verbose_name = "Consultation"
        verbose_name_plural = "Consultations"
        constraints = [
            models.UniqueConstraint(
                fields=["patient", "numero"],
                name="uniq_numero_consultation_par_patient",
            )
        ]

    @property
    def code(self):
        """Renvoie 'C1', 'C2', ..."""
        return f"C{self.numero}" if self.numero is not None else None

    def save(self, *args, **kwargs):
        """
        Attribue automatiquement un numero séquentiel PAR patient à la création.
        Simple + robuste : on tente, et en cas de collision (rare, concurrence), on ré-essaie.
        """
        is_creation = self.pk is None
        if is_creation and self.numero is None:
            for _ in range(3):  # petite boucle de retry en cas de course
                try:
                    with transaction.atomic():
                        dernier = (
                            Consultations.objects
                            .select_for_update()
                            .filter(patient=self.patient)
                            .aggregate(m=Max("numero"))["m"]
                        ) or 0
                        self.numero = dernier + 1
                        return super().save(*args, **kwargs)
                except IntegrityError:
                    # quelqu’un a pris le même numero entre-temps → on retente
                    self.numero = None
            # dernier essai sans verrou si besoin
        super().save(*args, **kwargs)


#-----------------------ORDONNANCE--------------------------------------------------------------------------------

from django.db.models import Max 
# === ORDONNANCE (minimale + compteur + liaison simple à une consultation) =====
class Ordonnance(models.Model):
    """
    Une ordonnance très simple :
    - Liée à un patient (un patient peut avoir N ordonnances)
    - Optionnellement liée à UNE consultation précise (une consultation a 0 ou 1 ordonnance)
    - Date de création automatique
    - Description : texte libre (le médecin y écrit toutes les lignes)
    - Numero : compteur automatique par patient (1, 2, 3, …)
    """

    # Patient concerné (obligatoire)
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,              # Si le patient est supprimé, on supprime ses ordonnances
        related_name="ordonnances",
        help_text="Patient auquel appartient cette ordonnance."
    )

    # Lier au besoin l’ordonnance à une consultation précise (facultatif)
    # OneToOne = garantit au niveau base qu’une consultation n’a AU PLUS qu’une ordonnance.
    consultation = models.OneToOneField(
        Consultations,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="ordonnance",             # Permet d’accéder via consultation.ordonnance (ou None)
        help_text="Consultation associée (facultatif : une consultation a au plus une ordonnance)."
    )

    # Compteur séquentiel PAR patient (1, 2, 3, …). On le calcule nous-mêmes à la création.
    numero = models.PositiveIntegerField(
        editable=False, null=True, blank=True,
        help_text="Numéro d’ordonnance séquentiel pour ce patient (attribué automatiquement)."
    )

    # Date/heure de création auto (pas besoin de la saisir)
    date_creation = models.DateTimeField(
        auto_now_add=True,
        help_text="Date et heure de création (remplie automatiquement)."
    )

    # Texte libre où le médecin décrit toute la prescription
    description = models.TextField(
        help_text="Contenu libre de l’ordonnance : médicaments, posologies, durées, consignes."
    )

    class Meta:
        # Empêche d’avoir deux ordonnances avec le même (patient, numero)
        constraints = [
            models.UniqueConstraint(
                fields=["patient", "numero"],
                name="uniq_numero_ordonnance_par_patient",
            )
        ]
        ordering = ["-date_creation", "-numero", "-id"]
        verbose_name = "Ordonnance"
        verbose_name_plural = "Ordonnances"

    def save(self, *args, **kwargs):
        """
        S’exécute à chaque sauvegarde (création ou modification).
        Logique ici :
          - Si c’est une CRÉATION (pas encore d’id) ET que le numéro n’est pas encore posé,
            on calcule le prochain numéro pour CE patient en regardant le max existant.
          - Ensuite on appelle super().save() pour laisser Django écrire en base.
        """
        is_creation = self.pk is None  # True si l’objet n’a pas encore été enregistré en base

        if is_creation and self.numero is None:
            # Récupérer le plus grand 'numero' déjà utilisé pour ce patient
            dernier_num = (
                Ordonnance.objects
                .filter(patient=self.patient)
                .aggregate(m=Max("numero"))["m"]
            ) or 0
            # Attribuer le prochain numéro
            self.numero = dernier_num + 1

        # Appel à la vraie sauvegarde Django (très important)
        super().save(*args, **kwargs)

    def __str__(self):
        """
        Représentation lisible dans l’admin et les listes :
        Ex : "ORD #3 - DUPONT Amina - 27/08/2025 14:32"
        """
        nom = f"{self.patient.nom} {self.patient.prenom or ''}".strip()
        return f"ORD #{self.numero} - {nom} - {self.date_creation.strftime('%d/%m/%Y %H:%M')}"