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
from django import forms
from .models import Patient,Consultation



class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['nom', 'prenom', 'age', 'telephone', 'email']
        
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du patient'
            }),
            'prenom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prénom du patient'
            }),
            'age': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Âge',
                'min': 0,
                'max': 120
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numéro de téléphone'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Adresse email (optionnel)'
            }),
        }
        
        labels = {
            'nom': 'Nom',
            'prenom': 'Prénom',
            'age': 'Âge',
            'telephone': 'Téléphone',
            'email': 'Email',
        }
    
    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age is not None and (age < 0 or age > 120):
            raise forms.ValidationError('L\'âge doit être compris entre 0 et 120 ans.')
        return age
    
    def clean_telephone(self):
        telephone = self.cleaned_data.get('telephone')
        if telephone and len(telephone) < 10:
            raise forms.ValidationError('Le numéro de téléphone doit contenir au moins 10 chiffres.')
        return telephone
    
#----------------------forms Consultation --------------------------------------------

# Dans votre fichier forms.py

from django import forms
from django.utils import timezone
from .models import Consultation, Patient

class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = [
            'patient', 'type', 'date_consultation', 
            'diagnostic', 'traitement', 'notes_medecin', 
            'prix', 'statut'
        ]
        widgets = {
            'patient': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'date_consultation': forms.DateTimeInput(attrs={
                'class': 'form-control', 
                'type': 'datetime-local',
                'required': True
            }),
            'diagnostic': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Saisissez le diagnostic...'
            }),
            'traitement': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Décrivez le traitement prescrit...'
            }),
            'notes_medecin': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Notes et observations du médecin...'
            }),
            'prix': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'statut': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Définir la date par défaut à maintenant si c'est une nouvelle consultation
        if not self.instance.pk:
            self.fields['date_consultation'].initial = timezone.now().strftime('%Y-%m-%dT%H:%M')
        
        # Ordonner les patients par nom
        self.fields['patient'].queryset = Patient.objects.all().order_by('nom', 'prenom')
        
        # Définir le statut par défaut
        if not self.instance.pk:
            self.fields['statut'].initial = 'planifie'
        
        # Ajouter des labels personnalisés
        self.fields['patient'].label = "Patient"
        self.fields['type'].label = "Type de consultation"
        self.fields['date_consultation'].label = "Date et heure"
        self.fields['statut'].label = "Statut"
        self.fields['diagnostic'].label = "Diagnostic"
        self.fields['traitement'].label = "Traitement prescrit"
        self.fields['notes_medecin'].label = "Notes du médecin"
        self.fields['prix'].label = "Prix (DH)"

    def clean_date_consultation(self):
        """Validation personnalisée pour la date de consultation"""
        date_consultation = self.cleaned_data.get('date_consultation')
        
        if date_consultation:
            # Vérifier que la date n'est pas trop ancienne (plus de 1 an)
            one_year_ago = timezone.now() - timezone.timedelta(days=365)
            if date_consultation < one_year_ago:
                raise forms.ValidationError("La date de consultation ne peut pas être antérieure à un an.")
        
        return date_consultation

    def clean_prix(self):
        """Validation personnalisée pour le prix"""
        prix = self.cleaned_data.get('prix')
        
        if prix is not None and prix < 0:
            raise forms.ValidationError("Le prix ne peut pas être négatif.")
        
        return prix