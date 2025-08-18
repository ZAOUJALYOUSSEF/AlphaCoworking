from flask_wtf import FlaskForm
from wtforms import (
    StringField, SelectField, TextAreaField, DateField, 
    TimeField, IntegerField, RadioField, BooleanField
)
from wtforms.validators import DataRequired, Email, Optional, NumberRange, ValidationError,Length
from datetime import datetime, timedelta

# Validateur personnalisé pour vérifier que la date de fin est après la date de début
def validate_end_date(form, field):
    if form.startDate.data and field.data:
        if field.data < form.startTate.data:
            raise ValidationError("La date de fin doit être après la date de début")

# Validateur pour les réservations horaires
def validate_hourly_booking(form, field):
    if form.bookingType.data == 'hourly':
        if not field.data:
            raise ValidationError("Ce champ est requis pour les réservations horaires")
        if form.startTime.data and form.endTime.data:
            if form.endTime.data <= form.startTime.data:
                raise ValidationError("L'heure de fin doit être après l'heure de début")

class BookingStep1Form(FlaskForm):
    bookingType = RadioField(
        'Type de réservation',
        choices=[
            ('hourly', 'À l\'heure'),
            ('daily', 'À la journée'),
            ('monthly', 'Au mois')
        ],
        validators=[DataRequired()],
        default='hourly'
    )

class BookingStep2Form(FlaskForm):
    spaceType = RadioField(
        'Type d\'espace',
        choices=[
            ('private', 'Bureau Privé'),
            ('open', 'Open Space'),
            ('meeting', 'Salle de Réunion')
        ],
        validators=[DataRequired()],
        default='private'
    )
    meetingCapacity = SelectField(
        'Capacité',
        choices=[
            ('8', '8 personnes'),
            ('15', '15 personnes'),
            ('23', '23 personnes')
        ],
        validators=[Optional()]
    )
    equipmentNeeds = SelectField(
        'Équipement supplémentaire',
        choices=[
            ('projector', 'Vidéoprojecteur'),
            ('whiteboard', 'Tableau blanc interactif'),
            ('catering', 'Service de restauration')
        ],
        validators=[Optional()],
        multiple=True
    )

class BookingStep3Form(FlaskForm):
    # Champs pour réservation horaire
    hourlyDate = DateField('Date', format='%Y-%m-%d', validators=[Optional()])
    startTime = TimeField('Heure de début', format='%H:%M', validators=[validate_hourly_booking])
    endTime = TimeField('Heure de fin', format='%H:%M', validators=[validate_hourly_booking])
    
    # Champs pour réservation journalière
    dailyStartDate = DateField('Date de début', format='%Y-%m-%d', validators=[Optional()])
    dailyEndDate = DateField('Date de fin', format='%Y-%m-%d', validators=[Optional(), validate_end_date])
    
    # Champs pour réservation mensuelle
    monthlyStartDate = DateField('Date de début', format='%Y-%m-%d', validators=[Optional()])
    monthlyDuration = SelectField(
        'Durée',
        choices=[
            ('1', '1 mois'),
            ('3', '3 mois (-5%)'),
            ('6', '6 mois (-10%)'),
            ('12', '12 mois (-15%)')
        ],
        validators=[Optional()]
    )

class BookingStep4Form(FlaskForm):
    fullName = StringField(
        'Nom complet',
        validators=[DataRequired(), Length(max=50)]
    )
    email = StringField(
        'Email',
        validators=[DataRequired(), Email(), Length(max=120)]
    )
    phone = StringField(
        'Téléphone',
        validators=[DataRequired(), Length(max=20)]
    )
    company = StringField(
        'Entreprise',
        validators=[Optional(), Length(max=50)]
    )
    notes = TextAreaField(
        'Demandes spéciales',
        validators=[Optional()]
    )

class BookingStep5Form(FlaskForm):
    paymentMethod = SelectField(
        'Méthode de paiement',
        choices=[
            ('credit', 'Carte de crédit'),
            ('transfer', 'Virement bancaire'),
            ('cash', 'Espèces (sur place)')
        ],
        validators=[DataRequired()]
    )
    termsCheck = BooleanField(
        'J\'accepte les conditions générales',
        validators=[DataRequired()]
    )
    newsletterCheck = BooleanField(
        'Je souhaite recevoir les offres promotionnelles'
    )

    # Champ caché pour le prix total
    totalPrice = StringField(validators=[DataRequired()])

    def validate(self, **kwargs):
        # Validation initiale
        if not super().validate():
            return False

        # Validation spécifique selon le type de réservation
        bookingType = self.bookingType.data

        if bookingType == 'hourly':
            if not all([self.hourlyDate.data, self.startTime.data, self.endTime.data]):
                self.hourlyDate.errors.append("Tous les champs sont requis pour une réservation horaire")
                return False

        elif bookingType == 'daily':
            if not all([self.dailyStartDate.data, self.dailyEndDate.data]):
                self.dailyStartDate.errors.append("Tous les champs sont requis pour une réservation journalière")
                return False

        elif bookingType == 'monthly':
            if not all([self.monthlyStartDate.data, self.monthlyDuration.data]):
                self.monthlyStartDate.errors.append("Tous les champs sont requis pour une réservation mensuelle")
                return False

        return True