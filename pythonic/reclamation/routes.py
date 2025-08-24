from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import current_user, login_required
from pythonic import db
from pythonic.models import Reclamation
from pythonic.reclamation.forms import ReclamationForm

reclamation_bp = Blueprint('reclamation_bp', __name__)

@reclamation_bp.route('/reclamation', methods=['GET', 'POST'])
def reclamation():
    form = ReclamationForm()
    if form.validate_on_submit():
        reclamation = Reclamation(
            client_name=form.client_name.data,
            client_email=form.client_email.data,
            title=form.title.data,
            description=form.description.data
        )
        db.session.add(reclamation)
        db.session.commit()
        flash('Votre réclamation a été envoyée avec succès.', 'success')
        return render_template('reclamation_form.html', form=ReclamationForm())
    return render_template('reclamation_form.html', form=form)

@reclamation_bp.route('/dashboard/reclamations')
@login_required
def dashboard_reclamations():
    if current_user.email != 'abdalas@alpha.coworking':
        abort(403)  # Accès interdit
    reclamations = Reclamation.query.order_by(Reclamation.created_at.desc()).all()
    return render_template('dashboard_reclamations.html', reclamations=reclamations)



@reclamation_bp.route('/dashboard/reclamations/<int:reclamation_id>')
@login_required
def reclamation_detail(reclamation_id):
    if current_user.email != 'abdalas@alpha.coworking':
        abort(403)

    # Récupère la réclamation
    reclamation = Reclamation.query.get_or_404(reclamation_id)

    # Change le statut si c'est "Nouvelle"
    if reclamation.status == 'Nouvelle':
        reclamation.status = 'Résolue'
        db.session.commit()

    return render_template('reclamation_detail.html', reclamation=reclamation)



@reclamation_bp.route('/dashboard/reclamations/<int:reclamation_id>/update_status', methods=['POST'])
@login_required
def update_status(reclamation_id):
    if current_user.email != 'abdalas@alpha.coworking':
        abort(403)

    reclamation = Reclamation.query.get_or_404(reclamation_id)
    new_status = request.form.get('status')

    if new_status in ['Nouvelle',  'Résolue']:
        reclamation.status = new_status
        db.session.commit()
        flash(f'Statut mis à jour : {new_status}', 'success')
    else:
        flash('Statut invalide', 'danger')

    return redirect(url_for('reclamation_bp.reclamation_detail', reclamation_id=reclamation_id))
