from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime,timedelta
from pythonic.models import Booking, db
from pythonic.reservation.forms import (
    BookingStep1Form, BookingStep2Form, BookingStep3Form,
    BookingStep4Form, BookingStep5Form
)
import json

booking_bp = Blueprint('reservation', __name__)


@booking_bp.route('/', methods=['POST','GET'])
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

            # Gestion des équipements supplémentaires
            if booking_data['space_type'] == 'meeting':
                print("\nTraitement équipements salle de réunion")
                equipment = request.form.getlist('equipmentNeeds')
                print("Équipements sélectionnés:", equipment)
                booking_data['additional_equipment'] = json.dumps(equipment) if equipment else None

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

            flash('Votre réservation a été enregistrée avec succès!', 'success')
            return redirect(url_for('reservation.booking_form'))

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
    
    return render_template('booking.html' )

@booking_bp.route('/dashboard/bookings')
@login_required
def admin_bookings():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', None)
    
    query = Booking.query.order_by(Booking.start_datetime.desc())
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    bookings = query.paginate(page=page, per_page=10)
    
    return render_template('booking.html',
                        bookings=bookings,
                        status_filter=status_filter,
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