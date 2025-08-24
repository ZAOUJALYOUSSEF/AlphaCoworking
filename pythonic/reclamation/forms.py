from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length,Optional

class ReclamationForm(FlaskForm):
    client_name = StringField('Votre nom', validators=[ Length(max=100),Optional()])
    client_email = StringField('Votre email', validators=[ Email(),Optional()])
    title = StringField('Titre', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Envoyer la réclamation')
