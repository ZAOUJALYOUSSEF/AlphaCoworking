from flask import Blueprint

admin_stats = Blueprint('admin_stats', __name__)

from pythonic.admin_view import routes