from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from pythonic.models import ContactMessage, db
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import or_

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
            flash('Votre message a été envoyé avec succès!', 'success')
            return redirect(url_for('contact.contact_form'))
        
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