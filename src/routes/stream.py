"""
Routes pour le streaming audio
"""

from flask import Blueprint, render_template, current_app
from flask_login import login_required

stream_bp = Blueprint('stream', __name__)

@stream_bp.route('/stream')
@login_required
def stream():
    """Page principale de streaming audio"""
    return render_template('stream.html', title='Stream')

@stream_bp.route('/api/stream')
@login_required
def stream_api():
    """API pour le streaming audio"""
    return {'status': 'success', 'message': 'Stream endpoint'}
