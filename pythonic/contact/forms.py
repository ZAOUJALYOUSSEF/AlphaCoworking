from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length
from pythonic.models import ContactMessage


class ContactForm(FlaskForm):
    full_name = StringField('Nom complet', validators=[
        DataRequired(message='Ce champ est obligatoire'),
        Length(min=2, max=50)
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Ce champ est obligatoire'),
        Email(message='Adresse email invalide')
    ])
    subject = SelectField('Sujet', choices=[
        ('', 'Choisissez un sujet'),
        ('Réservation', 'Réservation'),
        ('Question générale', 'Question générale'),
        ('Support technique', 'Support technique'),
        ('Autre', 'Autre')
    ], validators=[DataRequired(message='Veuillez sélectionner un sujet')])
    message = TextAreaField('Message', validators=[
        DataRequired(message='Ce champ est obligatoire'),
        Length(min=10, max=1000)
    ], render_kw={"rows": 5})


