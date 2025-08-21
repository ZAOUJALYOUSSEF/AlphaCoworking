from flask import render_template, Blueprint

# Crée un Blueprint pour les routes liées à la galerie (optionnel mais recommandé pour les gros projets)
galerie_bp = Blueprint('galerie', __name__)

@galerie_bp.route('/galerie')
def galerie():
    """Affiche la page de la galerie des espaces."""
    return render_template('galerie.html')

