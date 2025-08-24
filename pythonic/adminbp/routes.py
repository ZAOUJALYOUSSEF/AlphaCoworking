from flask import Blueprint, flash
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from pythonic import admin, db, bcrypt
from pythonic.models import User, Lesson, Course, Booking, ContactMessage, Reclamation
from flask_admin import AdminIndexView
from wtforms import PasswordField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, Optional
from flask_admin.form import BaseForm

adminbp = Blueprint("adminbp", __name__)

# Formulaire entièrement personnalisé pour User
class UserAdminForm(BaseForm):
    fname = StringField('First Name', validators=[DataRequired(), Length(min=2, max=25)])
    lname = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=25)])
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    image_file = StringField('Image File', default="default.png")
    bio = TextAreaField('Bio')
    new_password = PasswordField('New Password', 
        validators=[Optional(), Length(min=6)],
        description='Leave empty to keep current password'
    )

class UserModelView(ModelView):
    # Désactiver complètement la génération automatique du formulaire
    def scaffold_form(self):
        return UserAdminForm
    
    # Spécifier explicitement les colonnes du formulaire
    form_columns = ['fname', 'lname', 'username', 'email', 'image_file', 'bio', 'new_password']
    
    # Exclure le champ password de la base de données
    form_excluded_columns = ['password']
    
    # Liste des colonnes à afficher
    column_list = ['id', 'fname', 'lname', 'username', 'email', 'image_file']
    column_searchable_list = ['username', 'email', 'fname', 'lname']
    column_filters = ['username', 'email']
    
    def on_model_change(self, form, model, is_created):
        # Hasher le mot de passe seulement si le champ est rempli
        if form.new_password.data:
            model.password = bcrypt.generate_password_hash(form.new_password.data).decode("utf-8")
        elif is_created:
            # Pour les nouveaux utilisateurs, générer un mot de passe par défaut
            model.password = bcrypt.generate_password_hash('password123').decode("utf-8")
            flash('Default password set: password123', 'info')
    
    def is_accessible(self):
        return current_user.is_authenticated 

class MyModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated 

# Configuration des vues d'administration
admin.add_view(UserModelView(User, db.session))
admin.add_view(MyModelView(Booking, db.session))
admin.add_view(MyModelView(ContactMessage, db.session))
admin.add_view(MyModelView(Reclamation, db.session))