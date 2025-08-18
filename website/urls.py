from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    #path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),

#-----------------------Patient------------------------------------------
    path('liste_patients/', views.liste_patients, name='liste_patients'),
    path('patients/detail/<int:patient_id>/', views.detail_patient, name='detail_patient'),
    path('patients/ajouter/', views.ajouter_patient, name='ajouter_patient'),
    path('patients/modifier/<int:patient_id>/', views.modifier_patient, name='modifier_patient'),
    path('patients/supprimer/<int:patient_id>/', views.supprimer_patient, name='supprimer_patient'),




#-----------------------Consultation -------------------------------------------------------------------

    path('liste_consultations/', views.liste_consultations, name='liste_consultations'),
    path('ajouter/', views.ajouter_consultation, name='ajouter_consultation'),
    path('modifier/', views.modifier_consultation, name='modifier_consultation'),
    path('consultation/detail/<int:consultation_id>/', views.detail_consultation, name='detail_consultation'),
    path('consultation/supprimer/<int:consultation_id>/', views.supprimer_consultation, name='supprimer_consultation'),

]


