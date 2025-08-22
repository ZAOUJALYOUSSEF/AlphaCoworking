from datetime import datetime
from pythonic import db, login_manager
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(25), nullable=False)
    lname = db.Column(db.String(25), nullable=False)
    username = db.Column(db.String(25), unique=True, nullable=False)
    email = db.Column(db.String(125), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default="default.png")
    bio = db.Column(db.Text, nullable=True)
    password = db.Column(db.String(60), nullable=False)
    lessons = db.relationship("Lesson", backref="author", lazy=True)

    def get_reset_token(self):
        s = Serializer(current_app.config["SECRET_KEY"], salt="pw-reset")
        return s.dumps({"user_id": self.id})

    @staticmethod
    def verify_reset_token(token, age=3600):
        s = Serializer(current_app.config["SECRET_KEY"], salt="pw-reset")
        try:
            user_id = s.loads(token, max_age=age)["user_id"]
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.fname}', '{self.lname}', '{self.username}', '{self.email}', '{self.image_file}')"


class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    thumbnail = db.Column(
        db.String(20), nullable=False, default="default_thumbnail.jpg"
    )
    slug = db.Column(db.String(32), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)

    def __repr__(self):
        return f"Lesson('{self.title}', '{self.date_posted}')"


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(150), nullable=False)
    icon = db.Column(db.String(20), nullable=False, default="default_icon.jpg")
    lessons = db.relationship("Lesson", backref="course_name", lazy=True)

    def __repr__(self):
        return f"Course('{self.title}')"
    


class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date_submitted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='new')  # new, in_progress, resolved

    def __repr__(self):
        return f"ContactMessage('{self.full_name}', '{self.email}', '{self.subject}', '{self.date_submitted}')"
    


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    space_number = db.Column(db.String(20))  # Nouveau champ
    booking_type = db.Column(db.String(20), nullable=False)  # hourly, daily, monthly
    space_type = db.Column(db.String(20), nullable=True)    # Ajoutez cette ligne
    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # en heures, jours ou mois selon le type
    full_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    meeting_capacity = db.Column(db.String(10), nullable=True)
    company = db.Column(db.String(50))
    special_requests = db.Column(db.Text)
    payment_method = db.Column(db.String(30), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, confirmed, cancelled, completed
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    #additional_equipment = db.Column(db.JSON)  # Stocke les équipements supplémentaires
    created_by = db.Column(db.String(50), nullable=False,default="En ligne")  # ou "Bouchra" selon votre logique


    
    def __repr__(self):
        return f"Booking('{self.full_name}', '{self.booking_type}', '{self.start_datetime}', '{self.status}')"
    






class Reclamation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(100), nullable=True)
    client_email = db.Column(db.String(100), nullable=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Nouvelle')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"Reclamation('{self.title}', '{self.client_name}')"

