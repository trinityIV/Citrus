"""Routes d'authentification et de gestion des utilisateurs"""

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from ..models.user import User
from ..database import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Page d'inscription"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Ce nom d\'utilisateur existe déjà')
            return redirect(url_for('auth.register'))
        
        new_user = User(username=username)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash('Identifiants incorrects')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=remember)
        return redirect(url_for('main.index'))
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Déconnexion"""
    logout_user()
    return redirect(url_for('main.index'))

@auth_bp.route('/profile')
@login_required
def profile():
    """Page de profil"""
    return render_template('auth/profile.html')

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Édition du profil"""
    if request.method == 'POST':
        username = request.form.get('username')
        new_password = request.form.get('new_password')
        
        if username != current_user.username:
            if User.query.filter_by(username=username).first():
                flash('Ce nom d\'utilisateur existe déjà')
                return redirect(url_for('auth.edit_profile'))
            current_user.username = username
        
        if new_password:
            current_user.password = generate_password_hash(new_password, method='scrypt')
        
        db.session.commit()
        flash('Profil mis à jour avec succès')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/edit_profile.html')
