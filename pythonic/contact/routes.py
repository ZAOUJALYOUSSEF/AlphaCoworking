from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from pythonic.models import ContactMessage, db
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import or_
from flask_mail import Message
from flask import current_app
from threading import Thread
from pythonic import mail

contact = Blueprint('contact', __name__)

@contact.route('/', methods=['GET', 'POST'])
def contact_form():
    if request.method == 'POST':
        try:
            # Récupération des données avec des valeurs par défaut si nécessaire
            full_name = request.form.get('fullName', '').strip()
            email = request.form.get('email', '').strip()
            subject = request.form.get('subject', '').strip()
            message = request.form.get('message', '').strip()
            
            # Validation minimale
            if not all([full_name, email, subject, message]):
                flash('Tous les champs obligatoires doivent être remplis', 'danger')
                return redirect(url_for('contact.contact_form'))
            
            new_message = ContactMessage(
                full_name=full_name,
                email=email,
                subject=subject,
                message=message,
    
            )

            
            db.session.add(new_message)
            db.session.commit()
            message_id = new_message.id


            send_contact_email(full_name, email, subject, message)

            flash('Votre message a été envoyé avec succès!', 'success')
            return redirect(url_for('contact.confirmation', message_id=message_id))
        
        except Exception as e:
            db.session.rollback()
            flash(f"Une erreur est survenue: {str(e)}", 'danger')
            return redirect(url_for('contact.contact_form'))
    
    return render_template('contact.html')





@contact.route('/dashboard/messages')
@login_required
def admin_messages():
    page = request.args.get('page', 1, type=int)
    message_id = request.args.get('message_id', None, type=int)
    per_page = 5
    
    # Si un message_id est spécifié, afficher ce message seul
    if message_id:
        message = ContactMessage.query.get_or_404(message_id)
        # Marquer comme lu si c'est un nouveau message
        if message.status == 'new':
            message.status = 'in_progress'
            db.session.commit()
        return render_template('message_detail.html', message=message)
    
    # Sinon afficher la liste paginée
    messages = ContactMessage.query.order_by(ContactMessage.date_submitted.desc())\
                       .paginate(page=page, per_page=per_page)
    
    return render_template('contact.html', 
                         messages=messages,
                         active_tab='messages')



@contact.route('/messages/<int:message_id>/close', methods=['POST'])
@login_required
def mark_as_closed(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    message.status = 'closed'
    db.session.commit()
    flash('Message marqué comme traité', 'success')
    return redirect(url_for('contact.admin_messages', message_id=message_id))







@contact.route('/messages/confirmation/<int:message_id>')
def confirmation(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    return render_template('confirmation_contact.html', message=message)















def send_contact_email(full_name, email, subject, message_content):
    msg = Message(
        subject=f"Nouveau message de contact - {subject}",
        sender=("Votre Société", "zaouj2005@yandex.com"),
        recipients=["zaoujalyoussef3@gmail.com"]
    )
    
    msg.body = f"""
    Bonjour,
    
    Vous avez reçu un nouveau message via le formulaire de contact de votre site web.
    
    Informations du contact :
    - Nom complet : {full_name}
    - Adresse email : {email}
    - Sujet : {subject}
    
    Message :
    {message_content}
    
    ---
    Cet email a été généré automatiquement. Merci de ne pas y répondre directement.
    Pour répondre à ce message, veuillez utiliser l'adresse email fournie ci-dessus.
    """
    
    msg.html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #f8f9fa; padding: 15px; text-align: center; border-radius: 5px; }}
            .content {{ background-color: #fff; padding: 20px; border-radius: 5px; }}
            .footer {{ margin-top: 20px; padding: 15px; text-align: center; font-size: 12px; color: #6c757d; }}
            .info-label {{ font-weight: bold; color: #495057; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Nouveau message de contact</h2>
            </div>
            <div class="content">
                <p>Bonjour,</p>
                <p>Vous avez reçu un nouveau message via le formulaire de contact de votre site web.</p>
                
                <h4>Informations du contact :</h4>
                <p><span class="info-label">Nom complet :</span> {full_name}</p>
                <p><span class="info-label">Adresse email :</span> {email}</p>
                <p><span class="info-label">Sujet :</span> {subject}</p>
                
                <h4>Message :</h4>
                <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin: 10px 0;">
                    {message_content}
                </div>
            </div>
            <div class="footer">
                <p>Cet email a été généré automatiquement. Merci de ne pas y répondre directement.</p>
                <p>Pour répondre à ce message, veuillez utiliser l'adresse email fournie ci-dessus.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    mail.send(msg)
  