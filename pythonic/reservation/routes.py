from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime,timedelta
from pythonic.models import Booking, db
from pythonic.reservation.forms import (
    BookingStep1Form, BookingStep2Form, BookingStep3Form,
    BookingStep4Form, BookingStep5Form
)
import json
from sqlalchemy import or_, and_
from pythonic import mail
from flask_mail import Message
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from flask import send_file

from datetime import datetime
import os
import os

from sqlalchemy import cast, Date, or_, and_



from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch
from io import BytesIO
from flask import send_file





booking_bp = Blueprint('reservation', __name__)


@booking_bp.route('/reservation/', methods=['POST','GET'])
def booking_form():
    if request.method == 'POST':
        try:
            print("\n=== DEBUT DU TRAITEMENT ===")
            print("Données reçues du formulaire:", request.form)
            
            # Vérification des champs obligatoires
            required_fields = {
                'bookingType': 'Type de réservation',
                'spaceType': 'Type d\'espace',
                'fullName': 'Nom complet',
                'email': 'Email',
                'phone': 'Téléphone',
                'paymentMethod': 'Méthode de paiement',
                'totalPrice': 'Prix total'
            }
            
            missing_fields = []
            for field, name in required_fields.items():
                value = request.form.get(field)
                print(f"Champ {field} ({name}):", value)
                if not value:
                    missing_fields.append(name)
            
            if missing_fields:
                print("Champs obligatoires manquants:", missing_fields)
                flash(f'Champs obligatoires manquants: {", ".join(missing_fields)}', 'danger')
                return redirect(url_for('reservation.booking_form'))

            # Préparation des données
            booking_data = {
                'booking_type': request.form.get('bookingType'),
                'space_type': request.form.get('spaceType'),
                'full_name': request.form.get('fullName'),
                'email': request.form.get('email'),
                'phone': request.form.get('phone'),
                'company': request.form.get('company'),
                'special_requests': request.form.get('notes'),
                'payment_method': request.form.get('paymentMethod'),
                'status': 'pending'
            }

            # Gestion du prix total
            total_price = request.form.get('totalPrice')
            print("Prix total brut:", total_price)
            try:
                booking_data['total_price'] = float(total_price)
                print("Prix total converti:", booking_data['total_price'])
            except (ValueError, TypeError) as e:
                print("Erreur conversion prix total:", str(e))
                flash("Erreur dans le calcul du prix total", 'danger')
                return redirect(url_for('reservation.booking_form'))

            # Gestion des dates selon le type de réservation
            booking_type = booking_data['booking_type']
            print("Type de réservation:", booking_type)
            
            if booking_type == 'hourly':
                print("\nTraitement réservation horaire")
                date_str = request.form.get('hourlyDate')
                start_time = request.form.get('startTime')
                end_time = request.form.get('endTime')
                print(f"Date: {date_str}, Début: {start_time}, Fin: {end_time}")
                
                if not all([date_str, start_time, end_time]):
                    print("Champs date/heure manquants pour réservation horaire")
                    flash('Tous les champs de date/heure sont requis pour une réservation horaire', 'danger')
                    return redirect(url_for('reservation.booking_form'))
                
                try:
                    booking_data['start_datetime'] = datetime.strptime(f"{date_str} {start_time}", "%Y-%m-%d %H:%M")
                    booking_data['end_datetime'] = datetime.strptime(f"{date_str} {end_time}", "%Y-%m-%d %H:%M")
                    booking_data['duration'] = (booking_data['end_datetime'] - booking_data['start_datetime']).seconds // 3600
                    print("Dates converties avec succès")
                except ValueError as e:
                    print("Erreur conversion date/heure:", str(e))
                    flash("Format de date ou heure invalide", 'danger')
                    return redirect(url_for('reservation.booking_form'))
                
            elif booking_type == 'daily':
                print("\nTraitement réservation journalière")
                start_date = request.form.get('dailyStartDate')
                end_date = request.form.get('dailyEndDate')
                print(f"Date début: {start_date}, Date fin: {end_date}")
                
                if not all([start_date, end_date]):
                    print("Champs date manquants pour réservation journalière")
                    flash('Tous les champs de date sont requis pour une réservation journalière', 'danger')
                    return redirect(url_for('reservation.booking_form'))
                
                try:
                    booking_data['start_datetime'] = datetime.strptime(start_date, "%Y-%m-%d")
                    booking_data['end_datetime'] = datetime.strptime(end_date, "%Y-%m-%d")
                    booking_data['duration'] = (booking_data['end_datetime'] - booking_data['start_datetime']).days + 1
                    print("Dates journalières converties avec succès")
                except ValueError as e:
                    print("Erreur conversion date journalière:", str(e))
                    flash("Format de date invalide", 'danger')
                    return redirect(url_for('reservation.booking_form'))
                
            elif booking_type == 'monthly':
                print("\nTraitement réservation mensuelle")
                start_date = request.form.get('monthlyStartDate')
                duration = request.form.get('monthlyDuration')
                print(f"Date début: {start_date}, Durée: {duration} mois")
                
                if not all([start_date, duration]):
                    print("Champs manquants pour réservation mensuelle")
                    flash('Tous les champs sont requis pour une réservation mensuelle', 'danger')
                    return redirect(url_for('reservation.booking_form'))
                
                try:
                    booking_data['start_datetime'] = datetime.strptime(start_date, "%Y-%m-%d")
                    booking_data['duration'] = int(duration)
                    booking_data['end_datetime'] = booking_data['start_datetime'] + timedelta(days=30*booking_data['duration'])
                    print("Dates mensuelles converties avec succès")
                except ValueError as e:
                    print("Erreur conversion date mensuelle:", str(e))
                    flash("Format de date ou durée invalide", 'danger')
                    return redirect(url_for('reservation.booking_form'))


            # Debug final des données avant enregistrement
            print("\nDonnées complètes avant enregistrement:")
            for key, value in booking_data.items():
                print(f"{key}: {value} ({type(value)})")

            # Création de la réservation
            print("\nTentative de création de la réservation...")
            new_booking = Booking(**booking_data)
            db.session.add(new_booking)
            db.session.commit()
            print("Réservation enregistrée avec succès!")


            try:
                # Email de notification au propriétaire
                send_booking_notification(new_booking)
                print("Email de notification envoyé au propriétaire")
                
                # Email de confirmation au client
                send_booking_confirmation(new_booking)
                print("Email de confirmation envoyé au client")
                
            except Exception as email_error:
                print(f"Erreur lors de l'envoi des emails: {str(email_error)}")
                # Ne pas annuler la réservation si l'email échoue
                flash('Votre réservation a été enregistrée, mais il y a eu un problème avec l\'envoi des emails de confirmation.', 'warning')






            return redirect(url_for('reservation.confirmation', booking_id=new_booking.id))

        except ValueError as e:
            db.session.rollback()
            print("Erreur ValueError:", str(e))
            flash("Erreur de format dans les données soumises", 'danger')
            return redirect(url_for('reservation.booking_form'))
            
        except Exception as e:
            db.session.rollback()
            print("Erreur inattendue:", str(e))
            flash(f"Une erreur est survenue: {str(e)}", 'danger')
            return redirect(url_for('reservation.booking_form'))
    page = request.args.get('page', 1, type=int)
    bookings = Booking.query.order_by(Booking.start_datetime.desc()).paginate(page=page, per_page=10)
    
    return render_template('booking.html',bookings=bookings)


@booking_bp.route('/reservation/confirmation/<int:booking_id>')
def confirmation(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    return render_template('confirmation.html', booking=booking)



@booking_bp.route('/dashboard/bookings')
@login_required
def admin_bookings():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', None)
    search_query = request.args.get('search', None)
    date_filter = request.args.get('date', None)  # Nouveau filtre de date
    today_date = datetime.today().strftime('%Y-%m-%d')


    
    query = Booking.query.order_by(Booking.id.desc())
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    if search_query:
        query = query.filter(Booking.full_name.ilike(f'%{search_query}%'))
    bookings = query.paginate(page=page, per_page=10)
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
            from sqlalchemy import func, or_, and_

            # Nouvelle logique de filtrage qui fonctionne correctement
            query = query.filter(
                or_(
                    # Cas 1: La réservation commence ce jour-là
                    func.date(Booking.start_datetime) == filter_date,
                    # Cas 2: La réservation est en cours ce jour-là
                    and_(
                        func.date(Booking.start_datetime) <= filter_date,
                        func.date(Booking.end_datetime) >= filter_date
                    ),
                    # Cas 3: La réservation se termine ce jour-là (mais ne commence pas ce jour)
                    and_(
                        func.date(Booking.start_datetime) < filter_date,
                        func.date(Booking.end_datetime) == filter_date
                    )
                )
            )
        except ValueError:
            flash("Format de date invalide", "danger")
    bookings = query.paginate(page=page, per_page=10)


    return render_template('booking.html',
                        bookings=bookings,
                        status_filter=status_filter,
                        search_query=search_query,
                        date_filter=date_filter,
                        today_date=today_date,
                        active_tab='bookings')

@booking_bp.route('/dashboard/bookings/<int:booking_id>')
@login_required
def booking_detail(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    return render_template('booking_detail.html',
                         booking=booking,
                         active_tab='bookings')

@booking_bp.route('/dashboard/bookings/<int:booking_id>/update_status', methods=['POST'])
@login_required
def update_status(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    new_status = request.form.get('status')
    
    if new_status in ['pending', 'confirmed', 'cancelled', 'completed']:
        booking.status = new_status
        db.session.commit()
        flash("Statut de la réservation mis à jour", "success")
    else:
        flash("Statut invalide", "danger")
    
    return redirect(url_for('reservation.booking_detail', booking_id=booking_id))


























def send_booking_confirmation(booking):
    """Envoyer une confirmation de réservation au client avec un design moderne"""
    msg = Message(
        subject=f"✅ Confirmation de réservation",
        sender=("ALPHAWORKING", "alphaworking2@gmail.com"),
        recipients=[booking.email]
    )
    
    # Format des dates
    start_date = booking.start_datetime.strftime("%d/%m/%Y %H:%M") if booking.start_datetime else "N/A"
    end_date = booking.end_datetime.strftime("%d/%m/%Y %H:%M") if booking.end_datetime else "N/A"

    bank_details = ""
    if booking.payment_method.lower() == "transfer":
        bank_details = """
        <div class="section">
            <div class="section-title">
                <span>💰 Détails Bancaires</span>
            </div>
            <div class="info-value">
                Pour effectuer un virement bancaire, veuillez utiliser ces informations :<br>
                <strong>Intitulé du compte : Mr ABDALAS MOHAMED</strong><br>
                <strong>RIB: 230640464467021101180071</strong>


            </div>
        </div>
        """
    
    msg.html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Confirmation de Réservation</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 0;
                background-color: #f9f9f9;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: #ffffff;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px 20px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 600;
            }}
            .content {{
                padding: 30px;
            }}
            .section {{
                margin-bottom: 25px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 8px;
                border-left: 4px solid #667eea;
            }}
            .section-title {{
                color: #667eea;
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
            }}
            .section-title i {{
                margin-right: 10px;
                font-size: 20px;
            }}
            .info-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin-top: 15px;
            }}
            .info-item {{
                margin-bottom: 10px;
            }}
            .info-label {{
                font-weight: 600;
                color: #666;
                font-size: 14px;
                margin-bottom: 5px;
            }}
            .info-value {{
                color: #333;
                font-size: 16px;
            }}
            .status-badge {{
                display: inline-block;
                padding: 8px 16px;
                background: #ffc107;
                color: #333;
                border-radius: 20px;
                font-weight: 600;
                font-size: 14px;
            }}
            .total-price {{
                font-size: 24px;
                font-weight: 700;
                color: #28a745;
                text-align: center;
                margin: 20px 0;
            }}
            .footer {{
                background: #f1f3f4;
                padding: 25px;
                text-align: center;
                color: #666;
                font-size: 14px;
            }}
            .contact-info {{
                margin-top: 15px;
                padding: 15px;
                background: #e3f2fd;
                border-radius: 8px;
                text-align: center;
            }}
            .logo {{
                font-size: 24px;
                font-weight: bold;
                color: white;
                margin-bottom: 10px;
            }}
            @media (max-width: 600px) {{
                .info-grid {{
                    grid-template-columns: 1fr;
                }}
                .content {{
                    padding: 20px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">ALPHACoworking</div>
                <h1>Confirmation de Réservation</h1>
            </div>
            
            <div class="content">
                <p>Chère/Cher <strong>{booking.full_name}</strong>,</p>
                <p>Nous avons le plaisir de vous confirmer votre réservation. Voici le récapitulatif :</p>
                
                <div class="section">
                    <div class="section-title">
                        <span>📋 DÉTAILS DE LA RÉSERVATION</span>
                    </div>
                    <div class="info-grid">
                        <div class="info-item">
                            <div class="info-label">Type</div>
                            <div class="info-value">{'Par heure' if booking.booking_type.lower() == 'hourly' else 'Par mois' if booking.booking_type.lower() == 'monthly' else 'Par jour'}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Espace</div>
                            <div class="info-value">{'Bureau privé' if booking.space_type.lower() == 'private' else 'Open-space' if booking.space_type.lower() == 'open' else 'Salle de réunion'}</div>
                        </div>

                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">
                        <span>📅 CRÉNEAU RÉSERVÉ</span>
                    </div>
                    <div class="info-grid">
                        <div class="info-item">
                            <div class="info-label">Date de début</div>
                            <div class="info-value">{start_date}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Date de fin</div>
                            <div class="info-value">{end_date}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Durée</div>
                            <div class="info-value">{booking.duration} {'heure(s)' if booking.booking_type == 'hourly' else 'jour(s)' if booking.booking_type == 'daily' else 'mois'}</div>
                        </div>
                    </div>
                </div>
                
                <div class="total-price">
                    💶 Total: {booking.total_price} DH
                </div>
                
                <div class="section">
                    <div class="section-title">
                        <span>👤 VOS INFORMATIONS</span>
                    </div>
                    <div class="info-grid">
                        <div class="info-item">
                            <div class="info-label">Nom complet</div>
                            <div class="info-value">{booking.full_name}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Email</div>
                            <div class="info-value">{booking.email}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Téléphone</div>
                            <div class="info-value">{booking.phone}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Entreprise</div>
                            <div class="info-value">{booking.company or 'Non spécifié'}</div>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">
                        <span>💳 PAIEMENT</span>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Méthode de paiement</div>
                        <div class="info-value">{'Virement bancaire' if booking.payment_method.lower() == 'transfer' else 'Espèces'}</div>
                    </div>
                </div>
                {bank_details}

                
                {f'''
                <div class="section">
                    <div class="section-title">
                        <span>📝 DEMANDES SPÉCIALES</span>
                    </div>
                    <div class="info-value">
                        {booking.special_requests}
                    </div>
                </div>
                ''' if booking.special_requests else ''}
                
                <div class="contact-info">
                    <h3>📞 Besoin d'aide ?</h3>
                    <p>Email: <strong>alphacoworking2@gmail.com</strong></p>
                    <p>Téléphone: <strong>+212 6660-42749 / +212 5399-40885</strong></p>
                    <p>Horaires: Lundi-Dimache, 8h30-20h30</p>
                </div>
            </div>
            
            <div class="footer">
                <p>© 2025 Alphacoworking. Tous droits réservés.</p>
                <p>Cet email a été envoyé automatiquement, merci de ne pas y répondre.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Version texte simple pour les clients qui n'affichent pas le HTML
    msg.body = f"""
CHÈRE/CHER {booking.full_name.upper()},

CONFIRMATION DE VOTRE RÉSERVATION

Nous avons bien reçu votre demande de réservation et vous en remercions.

📋 DÉTAILS DE LA RÉSERVATION:
Référence: #{booking.id}
Type: {booking.booking_type}
Espace: {booking.space_type}
Statut: En attente de validation

📅 CRÉNEAU RÉSERVÉ:
Début: {start_date}
Fin: {end_date}
Durée: {booking.duration} {'heure(s)' if booking.booking_type == 'hourly' else 'jour(s)' if booking.booking_type == 'daily' else 'mois'}

💰 PRIX TOTAL: {booking.total_price} €

💳 MÉTHODE DE PAIEMENT: {booking.payment_method}

👤 VOS INFORMATIONS:
Nom: {booking.full_name}
Email: {booking.email}
Téléphone: {booking.phone}
Entreprise: {booking.company or 'Non spécifié'}

📝 DEMANDES SPÉCIALES:
{booking.special_requests or 'Aucune demande spéciale'}

📞 CONTACT:
Pour toute question, contactez-nous :
Email: contact@votresite.com
Téléphone: +33 1 23 45 67 89
Horaires: Lundi-Vendredi, 9h-18h

Votre réservation est actuellement en attente de validation finale.
Vous recevrez un email de confirmation une fois validée.

Merci pour votre confiance !

Cordialement,
L'équipe VotreEspace

---
Cet email a été envoyé automatiquement, merci de ne pas y répondre.
© 2024 VotreEspace. Tous droits réservés.
"""
    
    mail.send(msg)




def send_booking_notification(booking):
    """Envoyer une notification au propriétaire avec un design moderne"""
    msg = Message(
        subject=f"🚨 NOUVELLE RÉSERVATION - #{booking.id}",
        sender=("ALPHAWORKING", "alphaworking2@gmail.com"),
        recipients=["alphacoworking2@gmail.com"]
    )
    
    # Format des dates
    start_date = booking.start_datetime.strftime("%d/%m/%Y %H:%M") if booking.start_datetime else "N/A"
    end_date = booking.end_datetime.strftime("%d/%m/%Y %H:%M") if booking.end_datetime else "N/A"
    
    msg.html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Nouvelle Réservation</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 0;
                background-color: #fff5f5;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: #ffffff;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                border: 2px solid #e53e3e;
            }}
            .header {{
                background: linear-gradient(135deg, #e53e3e 0%, #dd6b20 100%);
                color: white;
                padding: 25px 20px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 26px;
                font-weight: 600;
            }}
            .alert-badge {{
                background: #fff;
                color: #e53e3e;
                padding: 8px 16px;
                border-radius: 20px;
                font-weight: bold;
                margin-top: 10px;
                display: inline-block;
            }}
            .content {{
                padding: 25px;
            }}
            .section {{
                margin-bottom: 20px;
                padding: 18px;
                background: #f7fafc;
                border-radius: 8px;
                border-left: 4px solid #e53e3e;
            }}
            .section-title {{
                color: #e53e3e;
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 12px;
                display: flex;
                align-items: center;
            }}
            .info-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 12px;
            }}
            .info-item {{
                margin-bottom: 8px;
            }}
            .info-label {{
                font-weight: 600;
                color: #718096;
                font-size: 13px;
                margin-bottom: 3px;
            }}
            .info-value {{
                color: #2d3748;
                font-size: 15px;
            }}
            .total-price {{
                font-size: 22px;
                font-weight: 700;
                color: #38a169;
                text-align: center;
                margin: 18px 0;
                padding: 12px;
                background: #f0fff4;
                border-radius: 8px;
            }}
            .footer {{
                background: #fed7d7;
                padding: 20px;
                text-align: center;
                color: #742a2a;
                font-size: 13px;
            }}
            @media (max-width: 600px) {{
                .info-grid {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚨 NOUVELLE RÉSERVATION</h1>
                <div class="alert-badge">Action requise</div>
            </div>
            
            <div class="content">
                <div class="section">
                    <div class="section-title">📋 RÉSERVATION #{booking.id}</div>
                    <div class="info-grid">
                        <div class="info-item">
                            <div class="info-label">Type</div>
                            <div class="info-value">{'Par heure' if booking.booking_type.lower() == 'hourly' else 'Par mois' if booking.booking_type.lower() == 'monthly' else 'Par jour'}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Espace</div>
                            <div class="info-value">{'Bureau privé' if booking.space_type.lower() == 'private' else 'Open-space' if booking.space_type.lower() == 'open' else 'Salle de réunion'}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Statut</div>
                            <div class="info-value">⏳ EN ATTENTE</div>
                        </div>
                    </div>
                </div>
                
                <div class="total-price">
                    💰 MONTANT: {booking.total_price} DH
                </div>
                
                <div class="section">
                    <div class="section-title">👤 CLIENT</div>
                    <div class="info-grid">
                        <div class="info-item">
                            <div class="info-label">Nom</div>
                            <div class="info-value">{booking.full_name}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Email</div>
                            <div class="info-value">{booking.email}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Téléphone</div>
                            <div class="info-value">{booking.phone}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Entreprise</div>
                            <div class="info-value">{booking.company or '-'}</div>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">📅 CRÉNEAU</div>
                    <div class="info-grid">
                        <div class="info-item">
                            <div class="info-label">Début</div>
                            <div class="info-value">{start_date}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Fin</div>
                            <div class="info-value">{end_date}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Durée</div>
                            <div class="info-value">{booking.duration} {'h' if booking.booking_type == 'hourly' else 'jr(s)' if booking.booking_type == 'daily' else 'mois'}</div>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">💳 PAIEMENT</div>
                    <div class="info-item">
                        <div class="info-label">Méthode</div>
                        <div class="info-value">{'Virement bancaire' if booking.payment_method.lower() == 'transfer' else 'Espèces'}</div>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <p>⚠️ Cette réservation nécessite une validation manuelle</p>
                <p>Connectez-vous à votre dashboard pour traiter cette demande</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    mail.send(msg)













@booking_bp.route('/dashboard/bookings/create', methods=['GET'])
@login_required
def create_booking():
    return render_template('create_booking.html', active_tab='bookings')
@booking_bp.route('/dashboard/bookings/save', methods=['POST'])
@login_required
def save_booking():
    try:
        # Récupération des données du formulaire
        booking_data = {
            'booking_type': request.form.get('bookingType'),
            'space_type': request.form.get('spaceType'),
            'space_number': request.form.get('spaceNumber'),  # Nouveau champ
            'start_datetime': datetime.strptime(request.form.get('startDatetime'), "%Y-%m-%dT%H:%M"),
            'end_datetime': datetime.strptime(request.form.get('endDatetime'), "%Y-%m-%dT%H:%M"),
            'full_name': request.form.get('fullName'),
            'email': request.form.get('email'),
            'meeting_capacity': request.form.get('meetingCapacity'),  # Nouveau champ
            'phone': request.form.get('phone'),
            'company': request.form.get('company'),
            'special_requests': request.form.get('specialRequests'),
            'payment_method': request.form.get('paymentMethod'),
            'total_price': float(request.form.get('totalPrice')),
            'status': request.form.get('status', 'pending'),
            'date_created': datetime.utcnow(),
            'created_by': request.form.get('createdBy')

        }

        if booking_data['space_number']:
            if check_space_availability(
                booking_data['space_number'],
                booking_data['start_datetime'],
                booking_data['end_datetime']
            ):
                flash("Cet espace n'est pas disponible pour la période sélectionnée", "danger")
                return redirect(url_for('reservation.create_booking'))

        # Calcul de la durée côté serveur
        start = booking_data['start_datetime']
        end = booking_data['end_datetime']
        diff = end - start
        if booking_data['booking_type'] == 'hourly':
            booking_data['duration'] = int(diff.total_seconds() // 3600)
        elif booking_data['booking_type'] == 'daily':
            booking_data['duration'] = int(diff.days) + 1
        elif booking_data['booking_type'] == 'monthly':
            months = (end.year - start.year) * 12 + (end.month - start.month)
            if end.day < start.day:
                months -= 1
            booking_data['duration'] = max(1, months)


        # Création et sauvegarde
        new_booking = Booking(**booking_data)
        db.session.add(new_booking)
        db.session.commit()

        flash("Réservation ajoutée avec succès !", "success")
        return redirect(url_for('reservation.admin_bookings'))

    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de l'ajout : {str(e)}", "danger")
        return redirect(url_for('reservation.create_booking'))













@booking_bp.route('/dashboard/bookings/<int:booking_id>/edit', methods=['GET'])
@login_required
def edit_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    return render_template('edit_booking.html', booking=booking, active_tab='bookings')

@booking_bp.route('/dashboard/bookings/<int:booking_id>/update', methods=['POST'])
@login_required
def update_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    original_space_number = booking.space_number
    try:
        booking.booking_type = request.form.get('bookingType')
        booking.space_type = request.form.get('spaceType')
        booking.space_number = request.form.get('spaceNumber')  # Mise à jour du numéro d'espace
        booking.start_datetime = datetime.strptime(request.form.get('startDatetime'), "%Y-%m-%dT%H:%M")
        booking.end_datetime = datetime.strptime(request.form.get('endDatetime'), "%Y-%m-%dT%H:%M")
        booking.full_name = request.form.get('fullName')
        booking.email = request.form.get('email')
        booking.phone = request.form.get('phone')
        booking.company = request.form.get('company')
        booking.special_requests = request.form.get('specialRequests')
        booking.payment_method = request.form.get('paymentMethod')
        booking.total_price = float(request.form.get('totalPrice'))
        booking.status = request.form.get('status')
        booking.meeting_capacity = request.form.get('meetingCapacity')  # Nouveau champ
        booking.created_by = request.form.get('createdBy')




        new_space_number = request.form.get('spaceNumber')
        if booking.space_type != 'meeting':
            booking.meeting_capacity = None
        if new_space_number != original_space_number or not original_space_number:
            if check_space_availability(
                new_space_number,
                booking.start_datetime,
                booking.end_datetime,
                booking.id
            ):
                flash("Cet espace n'est pas disponible pour la période sélectionnée", "danger")
                return redirect(url_for('reservation.edit_booking', booking_id=booking.id))
        # Recalcul de la durée
        start = booking.start_datetime
        end = booking.end_datetime
        diff = end - start
        if booking.booking_type == 'hourly':
            booking.duration = int(diff.total_seconds() // 3600)
        elif booking.booking_type == 'daily':
            booking.duration = int(diff.days) + 1
        elif booking.booking_type == 'monthly':
            months = (end.year - start.year) * 12 + (end.month - start.month)
            if end.day < start.day:
                months -= 1
            booking.duration = max(1, months)


        db.session.commit()
        flash("Réservation mise à jour avec succès !", "success")
        return redirect(url_for('reservation.booking_detail', booking_id=booking.id))

    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la mise à jour : {str(e)}", "danger")
        return redirect(url_for('reservation.edit_booking', booking_id=booking.id))




@booking_bp.route('/dashboard/bookings/<int:booking_id>/delete', methods=['GET'])
@login_required
def delete_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    try:
        db.session.delete(booking)
        db.session.commit()
        flash("Réservation supprimée avec succès !", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la suppression : {str(e)}", "danger")
    return redirect(url_for('reservation.admin_bookings'))


















def check_space_availability(space_number, start_datetime, end_datetime, exclude_booking_id=None):
    if not space_number:  # Si aucun espace n'est spécifié, on considère comme disponible
        return False

    query = Booking.query.filter(
        Booking.space_number == space_number,
        Booking.id != (exclude_booking_id if exclude_booking_id else 0),
        or_(
            and_(
                Booking.start_datetime <= end_datetime,
                Booking.end_datetime >= start_datetime
            ),
            and_(
                Booking.start_datetime >= start_datetime,
                Booking.end_datetime <= end_datetime
            ),
            and_(
                Booking.start_datetime <= start_datetime,
                Booking.end_datetime >= end_datetime
            )
        )
    )
    return query.first() is not None



@booking_bp.route('/api/check-space-availability', methods=['GET'])
@login_required
def check_space_availability_api():
    space_number = request.args.get('spaceNumber')
    start_datetime_str = request.args.get('startDatetime')
    end_datetime_str = request.args.get('endDatetime')
    booking_id = request.args.get('bookingId', None)

    try:
        start_datetime = datetime.strptime(start_datetime_str, "%Y-%m-%dT%H:%M")
        end_datetime = datetime.strptime(end_datetime_str, "%Y-%m-%dT%H:%M")
        available = not check_space_availability(space_number, start_datetime, end_datetime,
                                              int(booking_id) if booking_id else None)
        return jsonify({'available': available})
    except Exception as e:
        return jsonify(({'error': str(e)}), 400)


from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from datetime import datetime
from flask import send_file
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import os




def generate_invoice_pdf(booking):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=20*mm,
                           leftMargin=20*mm,
                           topMargin=20*mm,
                           bottomMargin=15*mm)

    styles = getSampleStyleSheet()

    # Styles personnalisés
    styles.add(ParagraphStyle(
        name='InvoiceTitle',
        fontSize=16,
        leading=20,
        alignment=1,  # Centré
        textColor=colors.HexColor('#2c3e50'),
        fontName='Helvetica-Bold'
    ))

    styles.add(ParagraphStyle(
        name='InvoiceSubtitle',
        fontSize=10,
        leading=14,
        alignment=1,  # Centré
        textColor=colors.HexColor('#7f8c8d')
    ))

    styles.add(ParagraphStyle(
        name='InvoiceHeader',
        fontSize=10,
        textColor=colors.HexColor('#34495e'),
        fontName='Helvetica-Bold'
    ))

    styles.add(ParagraphStyle(
        name='InvoiceNormalBold',
        fontSize=9,
        textColor=colors.black,
        fontName='Helvetica-Bold'
    ))

    styles.add(ParagraphStyle(
        name='InvoiceNormal',
        fontSize=9,
        textColor=colors.black,
        leading=12
    ))

    # Mettre à jour le style du footer pour centrer le texte
    styles.add(ParagraphStyle(
        name='InvoiceFooter',
        fontSize=8,
        alignment=1,  # Centré
        textColor=colors.HexColor('#95a5a6'),
        leading=10
    ))

    styles.add(ParagraphStyle(
        name='InvoiceSectionTitle',
        fontSize=11,
        textColor=colors.HexColor('#2c3e50'),
        fontName='Helvetica-Bold',
        spaceAfter=6
    ))

    # Style pour le montant total plus grand
    styles.add(ParagraphStyle(
        name='InvoiceTotal',
        fontSize=12,
        textColor=colors.black,
        fontName='Helvetica-Bold',
        leading=14
    ))

    story = []

    # En-tête avec les nouvelles informations de l'entreprise
    try:
        logo_path = "/static/logo.jpg"
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=1.8*inch, height=0.8*inch)
            logo.hAlign = 'LEFT'
            story.append(logo)
        else:
            company_header = Paragraph("<b>ALPHA-Coworking</b>", styles['InvoiceTitle'])
            story.append(company_header)
            company_sub = Paragraph("Espace de coworking premium pour professionnels exigeants. Conçu pour la productivité et l'inspiration.", styles['InvoiceSubtitle'])
            story.append(company_sub)
    except Exception as e:
        print(f"Erreur de logo: {e}")
        company_header = Paragraph("<b>ALPHAcoworking</b>", styles['InvoiceTitle'])
        story.append(company_header)
        company_sub = Paragraph("Espace de coworking premium pour professionnels exigeants. Conçu pour la productivité et l'inspiration.", styles['InvoiceSubtitle'])
        story.append(company_sub)

    story.append(Spacer(1, 0.3*inch))

    # Ligne de séparation
    story.append(Spacer(1, 2))
    separator = Table([[""]], colWidths=[7.2*inch], rowHeights=[1])
    separator.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
    ]))
    story.append(separator)
    story.append(Spacer(1, 0.2*inch))

    # Titre de la facture
    title_table = Table([
        [Paragraph("FACTURE", styles['InvoiceTitle'])]
    ], colWidths=[7.2*inch])
    title_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(title_table)

    # Informations de la facture et du client
    invoice_data = [
        [
            # Colonne informations facture
            Table([
                [Paragraph("<b>N° Facture:</b>", styles['InvoiceNormalBold']), Paragraph(f"INV-{booking.id:05d}", styles['InvoiceNormal'])],
                [Paragraph("<b>Date d'émission:</b>", styles['InvoiceNormalBold']), Paragraph(datetime.now().strftime("%d/%m/%Y"), styles['InvoiceNormal'])],
                [Paragraph("<b>Date de prestation:</b>", styles['InvoiceNormalBold']), Paragraph(booking.start_datetime.strftime("%d/%m/%Y"), styles['InvoiceNormal'])],
            ], colWidths=[1.8*inch, 2*inch], hAlign='LEFT'),

            # Colonne informations client
            Table([
                [Paragraph("<b>CLIENT</b>", styles['InvoiceHeader'])],
                [Paragraph(booking.full_name, styles['InvoiceNormal'])],
                [Paragraph(booking.email, styles['InvoiceNormal'])],
                [Paragraph(booking.phone, styles['InvoiceNormal'])],
                [Paragraph(booking.company or "Non spécifié", styles['InvoiceNormal'])],
            ], colWidths=[2.5*inch], hAlign='LEFT')
        ]
    ]

    invoice_table = Table(invoice_data, colWidths=[3.8*inch, 3.4*inch])
    invoice_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    story.append(invoice_table)

    # Détails de la prestation
    story.append(Paragraph("DÉTAIL DE LA PRESTATION", styles['InvoiceSectionTitle']))

    # Calculer le prix unitaire en fonction de la durée
    unit_price = booking.total_price
    if booking.duration > 1:
        unit_price = booking.total_price / booking.duration

    booking_details = [
        ["Description", "Quantité", "Prix unitaire", "Total"],
        [
            f"Réservation d'espace {booking.space_type.capitalize()} ({booking.booking_type})",
            f"{booking.duration} {'heure(s)' if booking.booking_type == 'hourly' else 'jour(s)' if booking.booking_type == 'daily' else 'mois'}",
            f"{unit_price:.2f} DH",
            f"{booking.total_price:.2f} DH"
        ]
    ]

    details_table = Table(booking_details, colWidths=[3.2*inch, 1.5*inch, 1.5*inch, 1.5*inch], repeatRows=1)
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e9ecef')),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('ALIGN', (2, 1), (3, 1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 0.1*inch))

    # Total sans TVA et sans SOUS-TOTAL
    total_data = [
        ["", Paragraph("<b>MONTANT TOTAL</b>", styles['InvoiceTotal']), Paragraph(f"<b>{booking.total_price:.2f} DH</b>", styles['InvoiceTotal'])]
    ]

    total_table = Table(total_data, colWidths=[3.2*inch, 1.5*inch, 1.5*inch])
    total_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('LINEABOVE', (2, 0), (2, 0), 1, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (2, 0), (2, -1), 20),
    ]))
    story.append(total_table)
    story.append(Spacer(1, 0.3*inch))

    # Pied de page professionnel avec les nouvelles informations et centré
    footer_text = (
        "ALPHAcoworking - Espace de coworking premium pour professionnels exigeants.<br/>"
        "Adresse: 39 Av. Sanhaja, Tanger 90060, Maroc<br/>"
        "Tél: +212 6660-42749, +212 5399-40885 - Email: alphacoworking2@gmail.com<br/>"
        "Horaires: Lun-Dim: 8h30 - 20h30<br/>"
        "© 2025 ALPHAcoworking - Tous droits réservés"
    )
    footer = Paragraph(footer_text, styles['InvoiceFooter'])
    story.append(footer)

    # Générer le PDF
    doc.build(story)
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"Facture_INV-{booking.id:05d}.pdf",
        mimetype='application/pdf'
    )


@booking_bp.route('/dashboard/bookings/<int:booking_id>/invoice', methods=['GET'])
@login_required
def generate_invoice(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    return generate_invoice_pdf(booking)




