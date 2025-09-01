from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms

class SignUpForm(UserCreationForm):
	email = forms.EmailField(label="", widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Email Address'}))
	first_name = forms.CharField(label="", max_length=100, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'First Name'}))
	last_name = forms.CharField(label="", max_length=100, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Last Name'}))


	class Meta:
		model = User
		fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')


	def __init__(self, *args, **kwargs):
		super(SignUpForm, self).__init__(*args, **kwargs)

		self.fields['username'].widget.attrs['class'] = 'form-control'
		self.fields['username'].widget.attrs['placeholder'] = 'User Name'
		self.fields['username'].label = ''
		self.fields['username'].help_text = '<span class="form-text text-muted"><small>Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.</small></span>'

		self.fields['password1'].widget.attrs['class'] = 'form-control'
		self.fields['password1'].widget.attrs['placeholder'] = 'Password'
		self.fields['password1'].label = ''
		self.fields['password1'].help_text = '<ul class="form-text text-muted small"><li>Your password can\'t be too similar to your other personal information.</li><li>Your password must contain at least 8 characters.</li><li>Your password can\'t be a commonly used password.</li><li>Your password can\'t be entirely numeric.</li></ul>'

		self.fields['password2'].widget.attrs['class'] = 'form-control'
		self.fields['password2'].widget.attrs['placeholder'] = 'Confirm Password'
		self.fields['password2'].label = ''
		self.fields['password2'].help_text = '<span class="form-text text-muted"><small>Enter the same password as before, for verification.</small></span>'	


# ----------------------------------patient---------------------------------------------------------

# forms.py
from django import forms
from .models import Patient

class PatientForm(forms.ModelForm):
    """
    Formulaire simple pour créer et modifier un patient
    Seulement les champs essentiels
    """
    
    class Meta:
        model = Patient
        
        # Seulement les champs essentiels
        fields = ['nom', 'prenom', 'date_naissance', 'sexe', 'telephone', 'email', 'adresse','profession', 'notes']
        
        # Style Bootstrap simple
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'sexe': forms.Select(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00 00 00 00 00'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemple.com'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Adresse'}),
            'profession': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Profession'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notes sur le patient'}),

        }
        
        # Labels simples
        labels = {
            'nom': 'Nom *',
            'prenom': 'Prénom',
            'date_naissance': 'Date de naissance',
            'sexe': 'Sexe',
            'telephone': 'Téléphone',
            'email': 'Email',
            'adresse': 'Adresse',
            'profession': 'Profession',
            'notes': 'Notes',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Le nom est obligatoire
        self.fields['nom'].required = True
    
#----------------------forms Consultation --------------------------------------------

# forms.py
from django import forms
from django.utils import timezone
from .models import Consultations, Patient

class ConsultationForm(forms.ModelForm):
    """
    Formulaire pour le modèle Consultations
    Compatible avec votre code JavaScript existant
    """
    
    class Meta:
        model = Consultations
        fields = [
            'patient',
            'type', 
            'date_consultation',
            'diagnostic',
            'statut'
        ]
        # Note: 'prix' est exclu car il sera calculé automatiquement
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configuration du champ patient
        self.fields['patient'].queryset = Patient.objects.all().order_by('nom', 'prenom')
        self.fields['patient'].widget = forms.Select(attrs={
            'class': 'form-select',
            'id': 'patient'
        })
        self.fields['patient'].empty_label = "Sélectionnez un patient"
        
        # Configuration du champ type
        self.fields['type'].widget = forms.Select(attrs={
            'class': 'form-select',
            'id': 'type'
        })
        
        # Configuration du champ date_consultation
        self.fields['date_consultation'].widget = forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'form-control',
                'id': 'date_consultation'
            }
        )
        # Valeur par défaut : maintenant
        if not self.instance.pk:  # Seulement pour les nouvelles consultations
            self.fields['date_consultation'].initial = timezone.now()
        
        # Configuration du champ diagnostic
        self.fields['diagnostic'].widget = forms.Textarea(attrs={
            'class': 'form-control',
            'id': 'diagnostic',
            'rows': 2,
            'placeholder': 'Diagnostic de la consultation...'
        })
        self.fields['diagnostic'].required = False
        
        # Configuration du champ statut
        self.fields['statut'].widget = forms.Select(attrs={
            'class': 'form-select',
            'id': 'statut'
        })
        self.fields['statut'].initial = 'planifie'
        
        # Labels en français
        self.fields['patient'].label = "Patient"
        self.fields['type'].label = "Type de consultation"
        self.fields['date_consultation'].label = "Date et heure"
        self.fields['diagnostic'].label = "Diagnostic"
        self.fields['statut'].label = "Statut"
        
        # Messages d'aide
        self.fields['type'].help_text = "Le prix sera calculé automatiquement selon le type choisi"
        self.fields['date_consultation'].help_text = "Format : JJ/MM/AAAA HH:MM"
    
    def clean_date_consultation(self):
        """
        Validation personnalisée pour la date de consultation
        """
        date_consultation = self.cleaned_data.get('date_consultation')
        
        if date_consultation:
            # Optionnel : vérifier que la date n'est pas trop dans le passé
            # (seulement un avertissement, pas une erreur bloquante)
            now = timezone.now()
            if date_consultation < now - timezone.timedelta(days=30):
                # Juste un warning, pas une erreur
                pass
        
        return date_consultation
    
    def clean(self):
        """
        Validation globale du formulaire
        """
        cleaned_data = super().clean()
        patient = cleaned_data.get('patient')
        date_consultation = cleaned_data.get('date_consultation')
        
        # Validation : un patient ne peut pas avoir 2 consultations à la même heure
        if patient and date_consultation:
            existing_consultation = Consultations.objects.filter(
                patient=patient,
                date_consultation=date_consultation
            )
            
            # Si on modifie une consultation existante, l'exclure de la vérification
            if self.instance.pk:
                existing_consultation = existing_consultation.exclude(pk=self.instance.pk)
            
            if existing_consultation.exists():
                raise forms.ValidationError(
                    f"Le patient {patient} a déjà une consultation programmée à cette date et heure."
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        """
        Sauvegarde personnalisée
        Le prix sera automatiquement calculé par la méthode save() du modèle
        """
        instance = super().save(commit=False)
        
        if commit:
            instance.save()
        
        return instance
    

#-----------------ORDONNANCE----------------------------------------------------------------

from .models import Ordonnance, Consultations

class OrdonnanceForm(forms.ModelForm):
    """
    Formulaire pour créer et modifier une ordonnance
    Compatible avec la logique existante des autres modules
    """
    
    class Meta:
        model = Ordonnance
        fields = [
            'patient',
            'consultation', 
            'description'
        ]
        # Note: 'numero' et 'date_creation' sont exclus car calculés automatiquement
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configuration du champ patient
        self.fields['patient'].queryset = Patient.objects.all().order_by('nom', 'prenom')
        self.fields['patient'].widget = forms.Select(attrs={
            'class': 'form-select',
            'id': 'patient'
        })
        self.fields['patient'].empty_label = "Sélectionnez un patient"
        
        # Configuration du champ consultation (optionnel)
        self.fields['consultation'].queryset = Consultations.objects.all().order_by('-date_consultation')
        self.fields['consultation'].widget = forms.Select(attrs={
            'class': 'form-select',
            'id': 'consultation'
        })
        self.fields['consultation'].empty_label = "Aucune consultation (optionnel)"
        self.fields['consultation'].required = False
        
        # Configuration du champ description
        self.fields['description'].widget = forms.Textarea(attrs={
            'class': 'form-control',
            'id': 'description',
            'rows': 8,
            'placeholder': 'Détaillez ici la prescription : médicaments, posologies, durées, consignes...'
        })
        
        # Labels en français
        self.fields['patient'].label = "Patient *"
        self.fields['consultation'].label = "Consultation associée"
        self.fields['description'].label = "Prescription"
        
        # Messages d'aide
        self.fields['patient'].help_text = "Patient pour lequel cette ordonnance est prescrite"
        self.fields['consultation'].help_text = "Optionnel : relier cette ordonnance à une consultation précise"
        self.fields['description'].help_text = "Décrivez tous les médicaments, posologies et consignes"
    
    def clean(self):
        """
        Validation globale du formulaire
        """
        cleaned_data = super().clean()
        patient = cleaned_data.get('patient')
        consultation = cleaned_data.get('consultation')
        
        # Validation : si une consultation est choisie, elle doit appartenir au bon patient
        if patient and consultation:
            if consultation.patient != patient:
                raise forms.ValidationError(
                    f"La consultation sélectionnée n'appartient pas au patient {patient}."
                )
        
        # Validation : si une consultation est choisie, elle ne peut avoir qu'une seule ordonnance
        if consultation:
            existing_ordonnance = Ordonnance.objects.filter(consultation=consultation)
            
            # Si on modifie une ordonnance existante, l'exclure de la vérification
            if self.instance.pk:
                existing_ordonnance = existing_ordonnance.exclude(pk=self.instance.pk)
            
            if existing_ordonnance.exists():
                raise forms.ValidationError(
                    f"Cette consultation a déjà une ordonnance associée."
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        """
        Sauvegarde personnalisée
        Le numero sera automatiquement calculé par la méthode save() du modèle
        """
        instance = super().save(commit=False)
        
        if commit:
            instance.save()
        
        return instance