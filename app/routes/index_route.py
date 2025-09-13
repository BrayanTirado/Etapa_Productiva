from flask import Blueprint, render_template
from datetime import datetime

bp = Blueprint('index_bp', __name__)

@bp.route('/')
def index():
    now = datetime.now()
    return render_template('index.html', now=now)
