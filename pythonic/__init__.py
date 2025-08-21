import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_ckeditor import CKEditor
from flask_modals import Modal
from flask_mail import Mail
from pythonic.config import Config
from flask_admin import Admin

db = SQLAlchemy()
bcrypt = Bcrypt()
migrate = Migrate(db)
login_manager = LoginManager()
ckeditor = CKEditor()
modal = Modal()
login_manager.login_view = "users.login"
login_manager.login_message_category = "info"
mail = Mail()
admin = Admin()

def nl2br(value):
    """Convertit les sauts de ligne en balises <br> pour HTML"""
    return value.replace('\n', '<br>') if value else ''

def create_app(config_calss=Config):
    app = Flask(__name__)
    app.config.from_object(Config)
    from pythonic.adminbp.routes import MyAdminIndexView

    # Ajout du filtre nl2br à l'environnement Jinja2
    app.jinja_env.filters['nl2br'] = nl2br

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    ckeditor.init_app(app)
    modal.init_app(app)
    mail.init_app(app)
    admin.init_app(app, index_view=MyAdminIndexView())

    from pythonic.main.routes import main
    from pythonic.users.routes import users
    from pythonic.lessons.routes import lessons
    from pythonic.courses.routes import courses_bp
    from pythonic.errors.handlers import errors
    from pythonic.adminbp.routes import adminbp
    from pythonic.contact.routes import contact
    from pythonic.reservation.routes import booking_bp
    from pythonic.admin_view.routes import admin_stats as admin_stats_blueprint

    from pythonic.reclamation.routes import reclamation_bp


    from pythonic.galerie.routes import galerie_bp
    app.register_blueprint(galerie_bp)

    app.register_blueprint(adminbp)
    app.register_blueprint(main)
    app.register_blueprint(users)
    app.register_blueprint(lessons)
    app.register_blueprint(courses_bp)
    app.register_blueprint(errors)
    app.register_blueprint(contact)
    app.register_blueprint(booking_bp)
    app.register_blueprint(admin_stats_blueprint)
    app.register_blueprint(reclamation_bp)



    return app