from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class ReclamationForm(FlaskForm):
    client_name = StringField('Votre nom', validators=[DataRequired(), Length(max=100)])
    client_email = StringField('Votre email', validators=[DataRequired(), Email()])
    title = StringField('Titre', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Envoyer la réclamation')
