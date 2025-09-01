from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required  # optionnel
from django.views.decorators.http import require_http_methods  # optionnel
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

# views.py - Vues pour gérer les patients
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Patient,Consultations
from .forms import PatientForm

def liste_patients(request):
    """
    Vue pour afficher la liste de tous les patients
    """
    
    # 1. Récupérer tous les patients de la base de données
    # order_by('-date_creation') = trier par date de création (le plus récent en premier)
    patients = Patient.objects.all().order_by('-date_creation')
    
    # 2. RECHERCHE - si l'utilisateur tape quelque chose dans la barre de recherche
    search_query = request.GET.get('search', '')  # Récupérer ce qui est tapé dans ?search=...
    if search_query:  # Si il y a quelque chose à chercher
        # Q() permet de faire des recherches complexes avec OU (|)
        # icontains = contient (insensible à la casse)
        patients = patients.filter(
            Q(nom__icontains=search_query) |        # Chercher dans le nom OU
            Q(prenom__icontains=search_query) |     # Chercher dans le prénom OU
            Q(telephone__icontains=search_query) |  # Chercher dans le téléphone OU
            Q(email__icontains=search_query)        # Chercher dans l'email
        )
    
    # 3. PAGINATION - diviser la liste en pages de 10 patients
    paginator = Paginator(patients, 10)  # 10 patients par page
    page_number = request.GET.get('page')  # Quelle page l'utilisateur veut voir
    page_obj = paginator.get_page(page_number)  # Récupérer les patients de cette page
    
    # 5. Envoyer les données au template
    context = {
        'patients': page_obj,              # Les patients à afficher
        'search_query': search_query,      # Pour garder le texte dans la barre de recherche
        'total_patients': patients.count() # Nombre total de patients trouvés
    }
    
    return render(request, 'patient/liste_patient.html', context)



def detail_patient(request, patient_id):
    """
    Vue pour afficher les détails d'UN patient spécifique
    """
    
    # Récupérer le patient avec cet ID, ou erreur 404 si il n'existe pas
    patient = get_object_or_404(Patient, id=patient_id)
    consultations = patient.consultations.all()  # déjà trié par Meta (récent → ancien)

    
    # Envoyer le patient au template
    context = {
        'patient': patient,
        'consultations': consultations,
    }
    
    return render(request, 'patient/detail_patient.html', context)




@login_required  # optionnel
@require_http_methods(["GET", "POST"])  # optionnel
def patient_form(request, patient_id=None):
    """
    Créer OU modifier un patient.
    - Si patient_id est None  -> création
    - Si patient_id est donné -> modification
    Utilise: template 'patient/form_patient.html' et PatientForm.
    """
    patient = get_object_or_404(Patient, id=patient_id) if patient_id else None

    if request.method == 'POST':
        form = PatientForm(request.POST or None, request.FILES or None, instance=patient)
        if form.is_valid():
            is_creation = patient is None
            patient = form.save()
            action = 'ajouté' if is_creation else 'modifié'
            # Ajustez les champs nom/prenom selon votre modèle
            messages.success(request, f'Le patient {patient.nom} {patient.prenom} a été {action} avec succès.')
            return redirect('liste_patients')
    else:
        form = PatientForm(instance=patient)

    context = {
        'form': form,
        'patient': patient,  # utile si le template affiche des infos en mode édition
        'title': 'Ajouter un Patient' if patient is None else 'Modifier le Patient',
    }
    return render(request, 'patient/form_patient.html', context)



def supprimer_patient(request, patient_id):
    """
    Vue pour supprimer un patient
    """
    
    # 1. Récupérer le patient à supprimer
    patient = get_object_or_404(Patient, id=patient_id)
    
    if request.method == 'POST':
        # L'utilisateur a confirmé la suppression
        
        # Garder le nom pour le message (car après .delete() on ne peut plus l'utiliser)
        nom_patient = f"{patient.nom} {patient.prenom}"
        
        # Supprimer définitivement de la base de données
        patient.delete()
        
        # Message de confirmation
        messages.success(request, f'Le patient {nom_patient} a été supprimé avec succès.')
        
        # Retourner à la liste
        return redirect('liste_patients')
    

    
    context = {
        'patient': patient
    }
    
    return render(request, 'patients/confirmer_suppression.html', context)











#------------------------Consultation.views-------------------------------------------------
# views.py - Version corrigée pour le modèle Consultations

from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .models import Consultations, Patient  # CORRECTION: Consultations au lieu de Consultation
from .forms import ConsultationForm


def liste_consultations(request):
    consultations = Consultations.objects.all().order_by('date_consultation')  # CORRECTION: Consultations

    search_query = request.GET.get('search', '')
    if search_query:
        consultations = consultations.filter(
            Q(patient__nom__icontains=search_query) |
            Q(patient__prenom__icontains=search_query) |
            Q(diagnostic__icontains=search_query)
            # SUPPRIMÉ: notes_medecin (n'existe pas dans le nouveau modèle)
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

    # CORRECTION: Référencer le bon modèle
    type_choices = Consultations.TYPE_CONSULTATION
    statut_choices = Consultations.STATUT_CONSULTATION

    context = {
        'consultations': page_obj,
        'search_query': search_query,
        'type_filter': type_filter,
        'statut_filter': statut_filter,
        'date_filter': date_filter,
        'type_choices': type_choices,
        'statut_choices': statut_choices,
        'total_consultations': consultations.count(),
        'patients': Patient.objects.all().order_by('nom', 'prenom'),
    }

    return render(request, 'consultation/liste_consultation.html', context)


def consultation_form(request, consultation_id=None):
    """
    Vue unifiée pour ajouter OU modifier une consultation dans une page séparée
    - Si consultation_id est None = Ajouter nouvelle consultation
    - Si consultation_id existe = Modifier consultation existante
    """
    # Déterminer si on modifie ou on ajoute
    consultation = None
    if consultation_id:
        consultation = get_object_or_404(Consultations, id=consultation_id)
    
    if request.method == 'POST':
        # === LOGIQUE DE TRAITEMENT (identique à vos vues existantes) ===
        
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
                
                # Créer le nouveau patient
                nouveau_patient = Patient.objects.create(
                    nom=nom,
                    prenom=prenom,
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
        if consultation:
            # MODIFICATION d'une consultation existante
            form = ConsultationForm(post_data, instance=consultation)
        else:
            # AJOUT d'une nouvelle consultation
            form = ConsultationForm(post_data)
        
        if form.is_valid():
            try:
                consultation_obj = form.save(commit=False)
                
                # Validation finale
                if isinstance(consultation_obj.patient, str) and consultation_obj.patient == 'new_patient':
                    messages.error(request, 'Erreur: patient non créé correctement')
                    return redirect('liste_consultations')
                
                # Sauvegarder (le prix sera calculé automatiquement)
                consultation_obj.save()
                
                # Message de succès selon l'action
                if consultation:
                    messages.success(request, 'Consultation modifiée avec succès!')
                else:
                    messages.success(request, 'Consultation ajoutée avec succès!')
                
                # Rediriger vers la liste
                return redirect('liste_consultations')
                
            except Exception as e:
                messages.error(request, f'Erreur lors de la sauvegarde: {str(e)}')
        else:
            # Afficher les erreurs du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
    # === AFFICHAGE DU FORMULAIRE (GET) ===
    
    # Récupérer les choix pour les selects
    type_choices = Consultations.TYPE_CONSULTATION
    statut_choices = Consultations.STATUT_CONSULTATION
    
    context = {
        'consultation': consultation,  # None pour ajout, objet pour modification
        'type_choices': type_choices,
        'statut_choices': statut_choices,
        'patients': Patient.objects.all().order_by('nom', 'prenom'),
    }
    
    return render(request, 'consultation/form_consultation.html', context)

def detail_consultation(request, consultation_id):
    """Voir les détails d'une consultation"""
    consultation = get_object_or_404(Consultations, id=consultation_id)  # CORRECTION: Consultations
    
    context = {
        'consultation': consultation,
    }
    
    return render(request, 'consultation/detail_consultation.html', context)


def supprimer_consultation(request, consultation_id):
    """Supprimer une consultation avec confirmation"""
    if request.method == 'POST':
        consultation = get_object_or_404(Consultations, id=consultation_id)  # CORRECTION: Consultations
        patient_name = str(consultation.patient)
        consultation.delete()
        messages.success(request, f'Consultation de {patient_name} supprimée avec succès!')
    
    return redirect('liste_consultations')

#---------------------------ORDONNANCE-----------------------------------------------
# À ajouter dans views.py - Vues pour gérer les ordonnances

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Ordonnance, Patient, Consultations
from .forms import OrdonnanceForm

def liste_ordonnances(request):
    """
    Vue pour afficher la liste de toutes les ordonnances
    Avec recherche et pagination
    """
    
    # 1. Récupérer toutes les ordonnances de la base de données
    # order_by('-date_creation') = trier par date de création (le plus récent en premier)
    ordonnances = Ordonnance.objects.select_related('patient', 'consultation').all().order_by('-date_creation')
    
    # 2. RECHERCHE - si l'utilisateur tape quelque chose dans la barre de recherche
    search_query = request.GET.get('search', '')  # Récupérer ce qui est tapé dans ?search=...
    if search_query:  # Si il y a quelque chose à chercher
        # Q() permet de faire des recherches complexes avec OU (|)
        # icontains = contient (insensible à la casse)
        ordonnances = ordonnances.filter(
            Q(patient__nom__icontains=search_query) |        # Chercher dans le nom du patient OU
            Q(patient__prenom__icontains=search_query) |     # Chercher dans le prénom du patient OU
            Q(description__icontains=search_query) |         # Chercher dans la description OU
            Q(numero__icontains=search_query)                # Chercher dans le numéro
        )
    
    # 3. PAGINATION - diviser la liste en pages de 15 ordonnances
    paginator = Paginator(ordonnances, 15)  # 15 ordonnances par page
    page_number = request.GET.get('page')  # Quelle page l'utilisateur veut voir
    page_obj = paginator.get_page(page_number)  # Récupérer les ordonnances de cette page
    
    # 4. Envoyer les données au template
    context = {
        'ordonnances': page_obj,              # Les ordonnances à afficher
        'search_query': search_query,         # Pour garder le texte dans la barre de recherche
        'total_ordonnances': ordonnances.count() # Nombre total d'ordonnances trouvées
    }
    
    return render(request, 'ordonnance/liste_ordonnance.html', context)


def detail_ordonnance(request, ordonnance_id):
    """
    Vue pour afficher les détails d'UNE ordonnance spécifique
    """
    
    # Récupérer l'ordonnance avec cet ID, ou erreur 404 si elle n'existe pas
    ordonnance = get_object_or_404(
        Ordonnance.objects.select_related('patient', 'consultation'), 
        id=ordonnance_id
    )
    
    # Envoyer l'ordonnance au template
    context = {
        'ordonnance': ordonnance,
    }
    
    return render(request, 'ordonnance/detail_ordonnance.html', context)


@login_required  # optionnel, si tu protèges l’accès
@require_http_methods(["GET", "POST"])
def ordonnance_form(request, ordonnance_id=None):
    """
    Vue unifiée pour ajouter OU modifier une ordonnance dans une page séparée
    - Si ordonnance_id est None = Ajouter nouvelle ordonnance
    - Si ordonnance_id existe = Modifier ordonnance existante
    """
    
    # Déterminer si on modifie ou on ajoute
    ordonnance = None
    if ordonnance_id:
        ordonnance = get_object_or_404(Ordonnance, id=ordonnance_id)
    
    if request.method == 'POST':
        # === LOGIQUE DE TRAITEMENT ===
        
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
                
                # Créer le nouveau patient
                nouveau_patient = Patient.objects.create(
                    nom=nom,
                    prenom=prenom,
                    telephone=None,
                    email=None
                )
                
                # Mettre à jour les données POST avec le nouvel ID patient
                post_data['patient'] = str(nouveau_patient.id)
                messages.success(request, f'Nouveau patient "{nom} {prenom}" créé avec succès!')
                
            except Exception as e:
                messages.error(request, f'Erreur lors de la création du patient: {str(e)}')
                return redirect('liste_ordonnances')
        
        # Créer le formulaire avec les données (potentiellement modifiées)
        if ordonnance:
            # MODIFICATION d'une ordonnance existante
            form = OrdonnanceForm(post_data, instance=ordonnance)
        else:
            # AJOUT d'une nouvelle ordonnance
            form = OrdonnanceForm(post_data)
        
        if form.is_valid():
            try:
                ordonnance_obj = form.save(commit=False)
                
                # Validation finale
                if isinstance(ordonnance_obj.patient, str) and ordonnance_obj.patient == 'new_patient':
                    messages.error(request, 'Erreur: patient non créé correctement')
                    return redirect('liste_ordonnances')
                
                # Sauvegarder (le numéro sera calculé automatiquement)
                ordonnance_obj.save()
                
                # Message de succès selon l'action
                if ordonnance:
                    messages.success(request, 'Ordonnance modifiée avec succès!')
                else:
                    messages.success(request, 'Ordonnance créée avec succès!')
                
                # Rediriger vers la liste
                return redirect('liste_ordonnances')
                
            except Exception as e:
                messages.error(request, f'Erreur lors de la sauvegarde: {str(e)}')
        else:
            # Afficher les erreurs du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
    # === AFFICHAGE DU FORMULAIRE (GET) ===
    
    context = {
        'ordonnance': ordonnance,  # None pour ajout, objet pour modification
        'patients': Patient.objects.all().order_by('nom', 'prenom'),
        'consultations': Consultations.objects.all().order_by('-date_consultation')[:50],  # Limiter aux 50 dernières
    }
    
    return render(request, 'ordonnance/form_ordonnance.html', context)



def supprimer_ordonnance(request, ordonnance_id):
    """Supprimer une consultation avec confirmation"""
    if request.method == 'POST':
        ordonnance = get_object_or_404(Ordonnance, id=ordonnance_id)
        patient_name = str(ordonnance.patient)
        ordonnance.delete()
        messages.success(request, f'Ordonnance de {patient_name} supprimée avec succès!')
    
    return redirect('liste_ordonnances')

#------imprimer ordonnace -----
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
import weasyprint
from .models import Ordonnance


def imprimer_ordonnance(request, pk):
    """
    Génère et retourne un PDF de l'ordonnance avec le design exact du modèle fourni.
    
    Args:
        request: HttpRequest
        pk: ID de l'ordonnance à imprimer
    
    Returns:
        HttpResponse: PDF de l'ordonnance
    """
    # Récupérer l'ordonnance ou retourner 404
    ordonnance = get_object_or_404(Ordonnance, pk=pk)
    
    # Construire l'URL de base pour les fichiers statiques
    # WeasyPrint a besoin d'URLs absolues pour accéder aux CSS et images
    base_url = request.build_absolute_uri('/').rstrip('/')
    
    # Préparer le contexte pour le template
    context = {
        'ordonnance': ordonnance,
        'patient': ordonnance.patient,
        'base_url': base_url,  # Pour résoudre les URLs statiques
        'STATIC_URL': settings.STATIC_URL,
    }
    
    # Rendre le template HTML avec les données
    html_string = render_to_string('prescriptions/ordonnance_pdf.html', context)
    
    # Créer le PDF avec WeasyPrint
    try:
        # Configuration WeasyPrint pour optimiser le rendu
        html = weasyprint.HTML(
            string=html_string,
            base_url=base_url,
            encoding='utf-8'
        )
        
        # Générer le PDF
        pdf = html.write_pdf()
        
        # Créer la réponse HTTP
        response = HttpResponse(pdf, content_type='application/pdf')
        
        # Nom du fichier téléchargé
        filename = f"Ordonnance_{ordonnance.patient.nom}_{ordonnance.numero}.pdf"
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        
        return response
        
    except Exception as e:
        # En cas d'erreur, retourner une réponse d'erreur simple
        return HttpResponse(
            f"Erreur lors de la génération du PDF: {str(e)}", 
            status=500,
            content_type='text/plain'
        )


def detail_ordonnance(request, pk):
    """
    Vue de détail d'une ordonnance (si elle n'existe pas déjà)
    """
    ordonnance = get_object_or_404(Ordonnance, pk=pk)
    context = {'ordonnance': ordonnance}
    return render(request, 'ordonnance/impression_ordonnance.html', context)