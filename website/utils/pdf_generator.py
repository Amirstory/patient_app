# utils/pdf_generator.py
"""
Générateur PDF professionnel pour les ordonnances médicales
Utilise ReportLab pour créer des PDFs selon les spécifications exactes
"""

import os
from datetime import datetime
from io import BytesIO

from django.conf import settings
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import black
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, KeepTogether
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.platypus import PageBreak
from reportlab.lib.utils import ImageReader


class OrdonnancePDFGenerator:
    """
    Classe principale pour générer les PDFs d'ordonnance
    Respecte exactement les spécifications fournies
    """
    
    def __init__(self, ordonnance):
        """
        Initialise le générateur avec une ordonnance
        
        Args:
            ordonnance: Instance du modèle Ordonnance
        """
        self.ordonnance = ordonnance
        self.patient = ordonnance.patient
        
        # === CONSTANTES DE MISE EN PAGE (selon spécifications) ===
        self.PAGE_WIDTH = 210 * mm   # A4 largeur
        self.PAGE_HEIGHT = 297 * mm  # A4 hauteur
        
        # Marges (spécifications exactes)
        self.MARGE_GAUCHE = 15 * mm
        self.MARGE_DROITE = 15 * mm  
        self.MARGE_HAUTE = 12 * mm
        self.MARGE_BASSE = 12 * mm
        
        # Largeur utile calculée
        self.LARGEUR_UTILE = self.PAGE_WIDTH - 30 * mm
        
        # Dimensions des zones (selon spécifications)
        self.HAUTEUR_HEADER = 30 * mm
        self.HAUTEUR_FOOTER = 20 * mm
        self.ESPACEMENT_LIGNES = 3 * mm
        
        # Chemins des images (à adapter selon votre structure)
        self.HEADER_IMAGE = os.path.join(settings.STATIC_ROOT or settings.STATICFILES_DIRS[0], 'images', 'entete.png')
        self.FOOTER_IMAGE = os.path.join(settings.STATIC_ROOT or settings.STATICFILES_DIRS[0], 'images', 'bas.png')
    
    def create_styles(self):
        """
        Crée les styles de texte selon les spécifications
        Police: Helvetica 11pt, interligne 14pt
        """
        styles = getSampleStyleSheet()
        
        # Style pour le texte principal (description)
        self.style_description = ParagraphStyle(
            'Description',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            leading=14,  # interligne 14pt
            leftIndent=0,
            rightIndent=0,
            spaceAfter=0,
            spaceBefore=0,
            alignment=TA_LEFT,
            textColor=black
        )
        
        # Style pour les informations patient (centré)
        self.style_info_centree = ParagraphStyle(
            'InfoCentree',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            leading=14,
            alignment=TA_CENTER,
            textColor=black
        )
        
        # Style pour les informations patient (gauche)
        self.style_info_gauche = ParagraphStyle(
            'InfoGauche',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            leading=14,
            alignment=TA_LEFT,
            textColor=black
        )
    
    def generate_pdf_response(self):
        """
        Génère le PDF et retourne une HttpResponse
        Méthode principale à appeler depuis la vue
        """
        # Créer un buffer en mémoire
        buffer = BytesIO()
        
        # Générer le PDF dans le buffer
        self.create_pdf(buffer)
        
        # Préparer la réponse HTTP
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        
        # Nom du fichier (pour le téléchargement)
        filename = f"Ordonnance_{self.patient.nom}_{self.ordonnance.numero}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    
    def create_pdf(self, buffer):
        """
        Crée le PDF complet selon les spécifications
        
        Args:
            buffer: Buffer où écrire le PDF
        """
        # Initialiser les styles
        self.create_styles()
        
        # Créer le document avec marges personnalisées
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=self.MARGE_GAUCHE,
            rightMargin=self.MARGE_DROITE,
            topMargin=self.MARGE_HAUTE,
            bottomMargin=self.MARGE_BASSE
        )
        
        # Construire le contenu
        story = self.build_content()
        
        # Générer le PDF avec template personnalisé
        doc.build(story, onFirstPage=self.draw_page, onLaterPages=self.draw_page)
    
    def build_content(self):
        """
        Construit le contenu principal de l'ordonnance
        """
        story = []
        
        # === ESPACEMENTS CALCULÉS (selon spécifications) ===
        # Espace après header + ligne + infos patient
        espace_apres_header = self.HAUTEUR_HEADER + self.ESPACEMENT_LIGNES + 8 * mm + 7 * mm + 6 * mm + 6 * mm
        
        # Ajouter l'espacement initial
        story.append(Spacer(1, espace_apres_header))
        
        # === TRAITEMENT DE LA DESCRIPTION ===
        description_lines = self.format_description()
        
        for line in description_lines:
            if line.strip():  # Ignorer les lignes vides
                # Ajouter des puces aux lignes principales (selon spécifications)
                if not line.startswith('- '):
                    line = f"• {line}"
                
                # Style avec indentation pour les sous-lignes
                if line.startswith('- '):
                    # Sous-ligne indentée de 6mm (selon spécifications)
                    style = ParagraphStyle(
                        'SousLigne',
                        parent=self.style_description,
                        leftIndent=6 * mm
                    )
                else:
                    style = self.style_description
                
                para = Paragraph(line, style)
                story.append(para)
            else:
                # Ligne vide = petit espacement
                story.append(Spacer(1, 4))
        
        return story
    
    def format_description(self):
        """
        Formate la description selon les spécifications
        Gère le word-wrap et les retours à la ligne
        """
        if not self.ordonnance.description:
            return ["Aucune description fournie."]
        
        # Séparer par lignes
        lines = self.ordonnance.description.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Vérifier si la ligne est trop longue (approximation)
                # ReportLab gérera le word-wrap automatiquement
                formatted_lines.append(line)
            else:
                formatted_lines.append("")  # Garder les lignes vides
        
        return formatted_lines
    
    def draw_page(self, canvas_obj, doc):
        """
        Dessine les éléments fixes de chaque page (header, footer, lignes)
        Cette méthode est appelée pour chaque page
        """
        # === COORDONNÉES CALCULÉES ===
        y_header_top = self.PAGE_HEIGHT - self.MARGE_HAUTE
        y_header_bottom = y_header_top - self.HAUTEUR_HEADER
        y_header_sep = y_header_bottom - self.ESPACEMENT_LIGNES
        
        y_footer_top = self.MARGE_BASSE + self.HAUTEUR_FOOTER
        y_footer_sep = y_footer_top + self.ESPACEMENT_LIGNES
        
        # === DESSINER LE HEADER ===
        if os.path.exists(self.HEADER_IMAGE):
            try:
                canvas_obj.drawImage(
                    self.HEADER_IMAGE,
                    self.MARGE_GAUCHE,
                    y_header_bottom,
                    width=self.LARGEUR_UTILE,
                    height=self.HAUTEUR_HEADER,
                    preserveAspectRatio=True,
                    anchor='sw'
                )
            except Exception as e:
                # Si l'image ne peut pas être chargée, dessiner un rectangle
                canvas_obj.setFillColor(black)
                canvas_obj.rect(self.MARGE_GAUCHE, y_header_bottom, self.LARGEUR_UTILE, self.HAUTEUR_HEADER)
                canvas_obj.drawString(self.MARGE_GAUCHE + 10, y_header_bottom + 10, f"Header manquant: {e}")
        
        # === LIGNE SÉPARATRICE HEADER ===
        canvas_obj.setStrokeColor(black)
        canvas_obj.setLineWidth(1)
        canvas_obj.line(self.MARGE_GAUCHE, y_header_sep, self.PAGE_WIDTH - self.MARGE_DROITE, y_header_sep)
        
        # === INFORMATIONS PATIENT (uniquement sur la première page) ===
        if canvas_obj.getPageNumber() == 1:
            self.draw_patient_info(canvas_obj, y_header_sep)
        
        # === DESSINER LE FOOTER ===
        if os.path.exists(self.FOOTER_IMAGE):
            try:
                canvas_obj.drawImage(
                    self.FOOTER_IMAGE,
                    self.MARGE_GAUCHE,
                    self.MARGE_BASSE,
                    width=self.LARGEUR_UTILE,
                    height=self.HAUTEUR_FOOTER,
                    preserveAspectRatio=True,
                    anchor='sw'
                )
            except Exception as e:
                # Si l'image ne peut pas être chargée
                canvas_obj.setFillColor(black)
                canvas_obj.rect(self.MARGE_GAUCHE, self.MARGE_BASSE, self.LARGEUR_UTILE, self.HAUTEUR_FOOTER)
                canvas_obj.drawString(self.MARGE_GAUCHE + 10, self.MARGE_BASSE + 10, f"Footer manquant: {e}")
        
        # === LIGNE SÉPARATRICE FOOTER ===
        canvas_obj.line(self.MARGE_GAUCHE, y_footer_sep, self.PAGE_WIDTH - self.MARGE_DROITE, y_footer_sep)
    
    def draw_patient_info(self, canvas_obj, y_header_sep):
        """
        Dessine les informations du patient (uniquement page 1)
        """
        canvas_obj.setFont("Helvetica", 11)
        
        # === LIGNE 1: DATE CENTRÉE ===
        date_aujourd_hui = datetime.now().strftime("%d/%m/%Y")
        texte_date = f"Casablanca le : {date_aujourd_hui}"
        
        # Calculer la largeur du texte pour le centrer
        text_width = canvas_obj.stringWidth(texte_date, "Helvetica", 11)
        x_centre = self.MARGE_GAUCHE + (self.LARGEUR_UTILE - text_width) / 2
        y_ligne1 = y_header_sep - 8 * mm
        
        canvas_obj.drawString(x_centre, y_ligne1, texte_date)
        
        # === LIGNE 2: NOM ET PRÉNOM (gauche) + ÂGE (droite) ===
        y_ligne2 = y_ligne1 - 7 * mm
        
        # Nom et prénom à gauche
        nom_prenom = f"Nom et prénom : {self.patient.nom} {self.patient.prenom or ''}".strip()
        canvas_obj.drawString(self.MARGE_GAUCHE, y_ligne2, nom_prenom)
        
        # Âge à droite (si disponible)
        if self.patient.age:
            texte_age = f"Âge : {self.patient.age} ans"
            age_width = canvas_obj.stringWidth(texte_age, "Helvetica", 11)
            x_age = self.PAGE_WIDTH - self.MARGE_DROITE - age_width
            canvas_obj.drawString(x_age, y_ligne2, texte_age)
        
        # === LIGNE SÉPARATRICE DES INFOS ===
        y_ligne_sep = y_ligne2 - 6 * mm
        canvas_obj.line(self.MARGE_GAUCHE, y_ligne_sep, self.PAGE_WIDTH - self.MARGE_DROITE, y_ligne_sep)