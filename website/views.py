from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import SignUpForm
from .models import Patient




def home(request):
	# Check to see if logging in
	if request.method == 'POST':
		username = request.POST['username']
		password = request.POST['password']
		# Authenticate
		user = authenticate(request, username=username, password=password)
		if user is not None:
			login(request, user)
			messages.success(request, "You Have Been Logged In!")
			return redirect('home')
		else:
			messages.success(request, "There Was An Error Logging In, Please Try Again...")
			return redirect('home')
	else:
		return render(request, 'home.html', )
	
def logout_user(request):
	logout(request)
	messages.success(request, "You Have Been Logged Out...")
	return redirect('home')

def register_user(request):
	if request.method == 'POST':
		form = SignUpForm(request.POST)
		if form.is_valid():
			form.save()
			# Authenticate and login
			username = form.cleaned_data['username']
			password = form.cleaned_data['password1']
			user = authenticate(username=username, password=password)
			login(request, user)
			messages.success(request, "You Have Successfully Registered! Welcome!")
			return redirect('home')
	else:
		form = SignUpForm()
		return render(request, 'register.html', {'form':form})

	return render(request, 'register.html', {'form':form})

#-----------------------------------Patients ----------------------------------------------------------

# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Patient
from .forms import PatientForm

def liste_patients(request):
    """Vue pour afficher la liste des patients avec recherche et filtre"""
    
    # Récupérer tous les patients
    patients = Patient.objects.all().order_by('-date_creation')
    
    # Gestion de la recherche
    search_query = request.GET.get('search', '')
    if search_query:
        patients = patients.filter(
            Q(nom__icontains=search_query) |
            Q(prenom__icontains=search_query) |
            Q(telephone__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Gestion du filtre par âge
    age_filter = request.GET.get('age_filter', '')
    if age_filter:
        if age_filter == 'enfant':
            patients = patients.filter(age__lt=18)
        elif age_filter == 'adulte':
            patients = patients.filter(age__gte=18, age__lt=65)
        elif age_filter == 'senior':
            patients = patients.filter(age__gte=65)
    
    # Pagination
    paginator = Paginator(patients, 10)  # 10 patients par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'patients': page_obj,
        'search_query': search_query,
        'age_filter': age_filter,
        'total_patients': patients.count()
    }
    
    return render(request, 'patient/liste_patient.html', context)

def detail_patient(request, patient_id):
    """Vue pour afficher les détails d'un patient"""
    patient = get_object_or_404(Patient, id=patient_id)
    
    context = {
        'patient': patient
    }
    
    return render(request, 'patient/detail_patient.html', context)

def ajouter_patient(request):
    """Vue pour ajouter un nouveau patient"""
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save()
            messages.success(request, f'Le patient {patient.nom} {patient.prenom} a été ajouté avec succès.')
            return redirect('liste_patients')
    else:
        form = PatientForm()
    
    context = {
        'form': form,
        'title': 'Ajouter un Patient'
    }
    
    return render(request, 'patient/form_patient.html', context)

def modifier_patient(request, patient_id):
    """Vue pour modifier un patient existant"""
    patient = get_object_or_404(Patient, id=patient_id)
    
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            patient = form.save()
            messages.success(request, f'Le patient {patient.nom} {patient.prenom} a été modifié avec succès.')
            return redirect('liste_patients')
    else:
        form = PatientForm(instance=patient)
    
    context = {
        'form': form,
        'patient': patient,
        'title': 'Modifier le Patient'
    }
    
    return render(request, 'patient/form_patient.html', context)


def supprimer_patient(request, patient_id):
    """Vue pour supprimer un patient"""
    patient = get_object_or_404(Patient, id=patient_id)
    
    if request.method == 'POST':
        nom_patient = f"{patient.nom} {patient.prenom}"
        patient.delete()
        messages.success(request, f'Le patient {nom_patient} a été supprimé avec succès.')
        return redirect('liste_patients')
    
    context = {
        'patient': patient
    }
    
    return render(request, 'patients/confirmer_suppression.html', context)

#------------------------Consultation -------------------------------------------

from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .models import Consultation, Patient
from .forms import ConsultationForm


def liste_consultations(request):
    consultations = Consultation.objects.all().order_by('date_consultation')

    search_query = request.GET.get('search', '')
    if search_query:
        consultations = consultations.filter(
            Q(patient__nom__icontains=search_query) |
            Q(patient__prenom__icontains=search_query) |
            Q(diagnostic__icontains=search_query) |
            Q(notes_medecin__icontains=search_query)
        )

    type_filter = request.GET.get('type_filter', '')
    if type_filter:
        consultations = consultations.filter(type=type_filter)

    statut_filter = request.GET.get('statut_filter', '')
    if statut_filter:
        consultations = consultations.filter(statut=statut_filter)

    date_filter = request.GET.get('date_filter', '')
    if date_filter:
        today = timezone.now().date()
        if date_filter == 'aujourd_hui':
            consultations = consultations.filter(date_consultation__date=today)
        elif date_filter == 'cette_semaine':
            start_week = today - timezone.timedelta(days=today.weekday())
            consultations = consultations.filter(date_consultation__date__gte=start_week)
        elif date_filter == 'ce_mois':
            consultations = consultations.filter(
                date_consultation__year=today.year,
                date_consultation__month=today.month
            )

    paginator = Paginator(consultations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Ici la correction importante
    type_choices = Consultation.TYPE_CONSULTATION
    statut_choices = Consultation.STATUT_CONSULTATION

    context = {
        'consultations': page_obj,
        'search_query': search_query,
        'type_filter': type_filter,
        'statut_filter': statut_filter,
        'date_filter': date_filter,
        'type_choices': type_choices,
        'statut_choices': statut_choices,
        'total_consultations': consultations.count(),
        'patients': Patient.objects.all().order_by('nom', 'prenom'),  # Ajoutez cette ligne

        # Pense à ajouter 'form' si tu utilises un formulaire dans la modal
        # 'form': ConsultationForm(),
    }

    return render(request, 'consultation/liste_consultation.html', context)




def ajouter_consultation(request):
    """Ajouter une nouvelle consultation"""
    if request.method == 'POST':
        # DEBUG: Afficher les données reçues
        
        
        # Vérifier si on doit créer un nouveau patient
        patient_id = request.POST.get('patient')
        new_patient_name = request.POST.get('new_patient_name')
        
        # Créer une copie des données POST pour modification
        post_data = request.POST.copy()
        
        if patient_id == 'new_patient' and new_patient_name:
            try:
                # Extraire nom et prénom du nom complet
                name_parts = new_patient_name.strip().split(' ', 1)
                nom = name_parts[0] if name_parts else 'Inconnu'
                prenom = name_parts[1] if len(name_parts) > 1 else ''
                
                
                # Créer le nouveau patient avec des valeurs par défaut
                nouveau_patient = Patient.objects.create(
                    nom=nom,
                    prenom=prenom,
                    age=None,
                    telephone=None,
                    email=None
                )
                
                
                # Mettre à jour les données POST avec le nouvel ID patient
                post_data['patient'] = str(nouveau_patient.id)
                messages.success(request, f'Nouveau patient "{nom} {prenom}" créé avec succès!')
                
            except Exception as e:
                messages.error(request, f'Erreur lors de la création du patient: {str(e)}')
                return redirect('liste_consultations')
        
        # Créer le formulaire avec les données (potentiellement modifiées)
        form = ConsultationForm(post_data)
        
        if form.is_valid():
            try:
                consultation = form.save(commit=False)
                
                # Si le patient est encore "new_patient", c'est une erreur
                if isinstance(consultation.patient, str) and consultation.patient == 'new_patient':
                    messages.error(request, 'Erreur: patient non créé correctement')
                    return redirect('liste_consultations')
                
                consultation.save()
                messages.success(request, 'Consultation ajoutée avec succès!')
                
            except Exception as e:
                messages.error(request, f'Erreur lors de la sauvegarde: {str(e)}')
        else:
            # DEBUG: Afficher les erreurs du formulaire
            for field, errors in form.errors.items():
                print(f"Champ '{field}': {errors}")
            
            # Afficher un message d'erreur détaillé
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            
            messages.error(request, f'Erreur dans le formulaire: {"; ".join(error_messages)}')
    
    return redirect('liste_consultations')


def modifier_consultation(request):
    """Modifier une consultation existante"""
    if request.method == 'POST':
        consultation_id = request.POST.get('consultation_id')
        if consultation_id:
            consultation = get_object_or_404(Consultation, id=consultation_id)
            
            # Vérifier si on doit créer un nouveau patient
            patient_id = request.POST.get('patient')
            new_patient_name = request.POST.get('new_patient_name')
            
            # Créer une copie des données POST pour modification
            post_data = request.POST.copy()
            
            if patient_id == 'new_patient' and new_patient_name:
                # Extraire nom et prénom du nom complet
                name_parts = new_patient_name.strip().split(' ', 1)
                nom = name_parts[0] if name_parts else 'Inconnu'
                prenom = name_parts[1] if len(name_parts) > 1 else ''
                
                # Créer le nouveau patient
                nouveau_patient = Patient.objects.create(
                    nom=nom,
                    prenom=prenom,
                    age=None,
                    telephone=None,
                    email=None
                )
                
                # Mettre à jour les données POST avec le nouvel ID patient
                post_data['patient'] = nouveau_patient.id
                messages.success(request, f'Nouveau patient "{nom} {prenom}" créé avec succès!')
            
            form = ConsultationForm(post_data, instance=consultation)
            if form.is_valid():
                form.save()
                messages.success(request, 'Consultation modifiée avec succès!')
            else:
                messages.error(request, 'Erreur dans le formulaire.')
    
    return redirect('liste_consultations')


def detail_consultation(request, consultation_id):
    """Voir les détails d'une consultation"""
    consultation = get_object_or_404(Consultation, id=consultation_id)
    
    context = {
        'consultation': consultation,
    }
    
    return render(request, 'consultation/detail_consultation.html', context)


def supprimer_consultation(request, consultation_id):
    """Supprimer une consultation avec confirmation"""
    if request.method == 'POST':
        consultation = get_object_or_404(Consultation, id=consultation_id)
        patient_name = str(consultation.patient)
        consultation.delete()
        messages.success(request, f'Consultation de {patient_name} supprimée avec succès!')
    
    return redirect('liste_consultations')