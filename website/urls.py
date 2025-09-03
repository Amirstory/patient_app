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
    path('patients/nouveau/', views.patient_form, name='ajouter_patient'),
    path('patients/<int:patient_id>/modifier/', views.patient_form, name='modifier_patient'),
    path('patients/supprimer/<int:patient_id>/', views.supprimer_patient, name='supprimer_patient'),




#-----------------------Consultation -------------------------------------------------------------------

    path('liste_consultations/', views.liste_consultations, name='liste_consultations'),
    path('consultation/nouveau/', views.consultation_form, name='ajouter_consultation'),
    path('consultation/<int:consultation_id>/modifier/', views.consultation_form, name='modifier_consultation'),
    path('consultation/detail/<int:consultation_id>/', views.detail_consultation, name='detail_consultation'),
    path('consultation/supprimer/<int:consultation_id>/', views.supprimer_consultation, name='supprimer_consultation'),


#-----------------------ORDONNANCE -------------------------------------------------------------------

    path('ordonnances/', views.liste_ordonnances, name='liste_ordonnances'),
    path('ordonnances/nouvelle/', views.ordonnance_form, name='nouvelle_ordonnance'),
    path('ordonnances/<int:ordonnance_id>/', views.detail_ordonnance, name='detail_ordonnance'),
    path('ordonnances/<int:ordonnance_id>/modifier/', views.ordonnance_form, name='modifier_ordonnance'),
    path('ordonnances/<int:ordonnance_id>/supprimer/', views.supprimer_ordonnance, name='supprimer_ordonnance'),
    path('ordonnances/<int:pk>/', views.detail_ordonnance, name='detail_ordonnance'),
    path("ordonnance/<int:ordonnance_id>/", views.generer_ordonnance, name="generer_ordonnance"),
]


