from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from functools import wraps
import firebase_admin
from firebase_admin import auth

auth_bp = Blueprint('auth', __name__)

# --- THE PROTECTOR DECORATOR ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated_function

# --- ROUTES ---
@auth_bp.route('/login')
def login_page():
    return render_template('login.html') # We will make this next

@auth_bp.route('/api/login', methods=['POST'])
def token_login():
    data = request.json
    id_token = data.get('idToken')
    try:
        # Verify the token sent from the browser (works for both Email & Google)
        decoded_token = auth.verify_id_token(id_token)
        session['user'] = decoded_token['email']
        return jsonify({'success': True})
    except:
        return jsonify({'success': False}), 401

@auth_bp.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))