from flask import Blueprint, render_template, request, session, redirect, url_for, flash, abort
from functools import wraps
import os
import db_manager
from werkzeug.security import check_password_hash,generate_password_hash

auth_bp = Blueprint('auth', __name__)

# --- THE PROTECTOR DECORATOR ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin'):
            abort(401, description="Admin login required to modify tournaments.")
        return f(*args, **kwargs)
    return decorated_function

# --- ROUTES ---
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_input = request.form.get('username')
        password_input = request.form.get('password')

        # 1. Try Live Firebase Login First
        stored_hash = db_manager.get_admin_password(username_input)
        if stored_hash and check_password_hash(stored_hash, password_input):
            session['admin'] = True      
            session['user'] = username_input   
            flash(f"Welcome back, {session['user']}!", "success")
            return redirect(url_for('dashboard'))

        # 2. Try .env Fallback / First-Time Setup
        env_user = os.getenv('ADMIN_USERNAME')
        env_pass = os.getenv('ADMIN_PASSWORD')

        if username_input == env_user and password_input == env_pass:
            # Check if this admin is already in Firebase
            if not stored_hash:

                new_hash = generate_password_hash(password_input)
                db_manager.save_admin_to_db(username_input, new_hash)
                flash("First-time setup complete: Credentials synced to database.", "info")
            
            session['admin'] = True      
            session['user'] = username_input   
            flash(f"Welcome back, {session['user']}!", "success")
            return redirect(url_for('dashboard'))

        flash("Invalid Username or Password", "error")
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have logged out.", "info")
    return redirect(url_for('index'))